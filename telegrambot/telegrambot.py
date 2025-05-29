from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update, ReplyKeyboardMarkup, nest_asyncio
import logging, os, ssl, asyncio, json
from aiomqtt import Client

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.basicConfig(format='%(asctime)s - TelegramBot - %(levelname)s - %(message)s', level=logging.INFO) 

def crear_cliente_mqtt():
    """Returns:
            Client: A Mqtt client configured to connect to the server specified by the environment variables."""
    logging.info("Creando cliente MQTT para el servidor: " + os.environ["SERVIDOR"] + ":" + os.environ["PUERTO_MQTTS"])

    tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    tls_context.minimum_version = ssl.TLSVersion.TLSv1_2
    tls_context.maximum_version = ssl.TLSVersion.TLSv1_3
    tls_context.verify_mode = ssl.CERT_REQUIRED
    tls_context.check_hostname = True
    tls_context.load_default_certs()

    return Client(
        hostname=os.environ["SERVIDOR"],
        username=os.environ["MQTT_USR"],
        password=os.environ["MQTT_PASS"],
        port=int(os.environ["PUERTO_MQTTS"]),
        tls_context=tls_context)

async def oyente_mqtt(application):
    """Listens for MQTT messages and updates the bot data with the received values.
    Args:
        application (Application): The Telegram bot application instance.
    """
    logging.info("Escuchando al servidor MQTT: " + os.environ["SERVIDOR"] + ":" + os.environ["PUERTO_MQTTS"])

    client = crear_cliente_mqtt()

    async with client as c:
        await c.subscribe(f"{os.environ['ID_DISPOSITIVO']}")
        async for message in c.messages:
            try:
                payload = json.loads(message.payload.decode())
                logging.info(f"Mensaje recibido en el topic {message.topic}: {payload}")
                application.bot_data['temperatura'] = payload.get('temperatura')
                application.bot_data['humedad'] = payload.get('humedad')
                application.bot_data['setpoint'] = payload.get('setpoint')
                application.bot_data['modo'] = payload.get('modo')
                application.bot_data['periodo'] = payload.get('periodo')
                application.bot_data['rele'] = payload.get('rele')
            except json.JSONDecodeError as e:
                logging.error(f"Error al decodificar JSON: {e}")

async def sin_autorizacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles unauthorized access attempts by sending a message to the user."""

    logging.info("Intento de conexión de: " + str(update.message.from_user.id))
    logging.info(context)
    logging.info(context.application)
    logging.info(context.application.handlers)
    logging.info(context.application.handlers[0])
    logging.info(context.application.handlers[0][0])
    logging.info(context.application.handlers[0][0].filters)
    logging.info(context.application.handlers[0][0].filters.invfilters)
    logging.info(context.application.handlers[0][0].filters.invfilters[0]) 
    # Hallar que significa toda esta información que el bot de telegram le saca de los usuarios no autorizados
    # Se puede cambiar de manera dinámica los usuarios autorizados

    await context.bot.send_message(chat_id=update.effective_chat.id, text="No estas autorizado autorizado")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command by welcoming the user and providing a keyboard with options."""

    logging.info("Se conectó: " + str(update.message.from_user.id))
    if update.message.from_user.first_name:
        nombre=update.message.from_user.first_name
    else:
        nombre=""
    if update.message.from_user.last_name:
        apellido=update.message.from_user.last_name
    else:
        apellido=""
    kb = [["/temperatura_humedad"],["/rele"],["/modo automatico"],["/modo manual"], ["/destello"]]

    await context.bot.send_message(update.message.chat.id, 
                                   text="Bienvenido al Bot "+ nombre + " " + apellido + 
                                   '\nUtiliza el comando "acercade" para más información de como usar el Bot'
                                   + '\nUtiliza el comando "config" para obtemer la configuración de la Raspberry Pi Pico',
                                   reply_markup=ReplyKeyboardMarkup(kb))

async def acercade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /acercade command by providing information about the bot and its commands."""
    
    logging.info("se solicitó información del Bot")
    await context.bot.send_message(update.message.chat.id, 
                                   text="Comandos que tiene el Bot:\n" +
                                        "Comando                            -   Descripción\n" +
                                        "/periodo <tiempo>          -   Tiempo de sensado de datos\n" +
                                        "/setpoint <temperatura>    -   Si es superada esta temperatura se activa el Rele\n" +
                                        "\nAdemás puedes utilizar el teclado virtual para:\n" +
                                        "mediciones                 -   Te muestra la última temperatura y humedad registrada\n" +
                                        "rele                       -   Enciende o apaga el rele\n" +
                                        "destello                   -   Destella un led por un tiempo\n" +
                                        "modo                       -   Cambia el modo de operación del rele\n")

async def config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /config command by providing the current configuration of the Raspberry Pi Pico."""

    logging.info("se solicitó la configuración de la Raspberry Pi Pico")
    if 'rele' not in context.bot_data:
        await context.bot.send_message(update.message.chat.id,
                                   text="No se ha recibido la configuración de la Raspberry Pi Pico, por favor, inténtalo más tarde.")
        return

    rele = "Encendido" if context.bot_data['rele'] == 0 else "Apagado"
    modo_operacion = "Manual" if context.bot_data['modo'] == 0 else "Automático"

    await context.bot.send_message(update.message.chat.id, 
                                   text="La configuración de la Raspberry Pi Pico es:\n" +
                                        "Nombre del dispositivo: " + str(os.environ["ID_DISPOSITIVO"]) + 
                                        "\nEl modo del Rele es: " + rele +
                                        "\nEl periodo de sensado es: " + str(context.bot_data['periodo']) +
                                        "\nEl modo de operación del rele es: " + modo_operacion +
                                        "\nEl setpoint de temperatura es: " + str(context.bot_data['setpoint']))

async def temperatura_humedad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /temperatura_humedad command by sending the current temperature and humidity data."""

    logging.info("Se solicitó la temperatura y humedad actual")
    if 'temperatura' in context.bot_data and 'humedad' in context.bot_data:
        temperatura = context.bot_data['temperatura']
        humedad = context.bot_data['humedad']
        await context.bot.send_message(update.message.chat.id, 
                                       text=f"Temperatura: {temperatura} °C\nHumedad: {humedad} %")
    else:
        await context.bot.send_message(update.message.chat.id, 
                                       text="No se dispone de datos de temperatura y humedad en este momento.")

async def publicar_datos_mqtt(cliente, topico, valor):
    """Publishes data to an MQTT topic.
    Args:
        cliente (str): The MQTT client identifier.
        topico (str): The MQTT topic to publish to.
        valor : The value to publish.
    """
    async with cliente as c:
            await c.publish(f'{os.environ["ID_DISPOSITIVO"]}/{topico}', str(valor))

async def setpoint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /setpoint command by setting the temperature setpoint for the bot."""

    logging.info("Se intenta de modificar el setpoint de temperatura")
    logging.info(context.args)
    if context.args:
        try:
            setpoint = float(context.args[0])
            if setpoint >= 0:
                await publicar_datos_mqtt(context.bot_data['mqtt'], 'setpoint', setpoint)
                
                context.bot_data['setpoint'] = setpoint

                logging.info("Se modificó el setpoint de temperatura a: " + str(setpoint))

                await context.bot.send_message(update.message.chat.id, 
                                               text=f"El setpoint de temperatura es: {setpoint} °C")
            else:
                await context.bot.send_message(update.message.chat.id, 
                                               text="El setpoint de temperatura debe ser mayor o igual a 0")
        except ValueError:
            await context.bot.send_message(update.message.chat.id, 
                                           text="El setpoint de temperatura debe ser un número válido")

async def periodo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /periodo command by setting the sensing period for the bot."""

    logging.info("Se intenta de modificar el periodo de sensado")
    logging.info(context.args)
    if context.args:
        try:
            periodo=int(context.args[0])
            if periodo > 0:
                await publicar_datos_mqtt(context.bot_data['mqtt'], 'periodo', periodo)
                            
                context.bot_data['periodo'] = periodo

                logging.info("Se modificó el periodo de sensado a: " + str(periodo))

                await context.bot.send_message(update.message.chat.id, 
                                               text=f"El periodo de sensado es: {periodo} segundos")
            else:
                await context.bot.send_message(update.message.chat.id, 
                                               text="El periodo de sensado debe ser mayor a 0")
        except ValueError:
            await context.bot.send_message(update.message.chat.id, 
                                           text="El periodo de sensado debe ser un número entero")

async def modo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /modo command by changing the mode of operation for the bot."""

    logging.info("Se intenta de modificar el modo de operación del rele")
    if context.args:
        modo = context.args[0].lower()
        if modo in ['manual', 'automatico']:
            m = 0 if modo == 'manual' else 1

            await publicar_datos_mqtt(context.bot_data['mqtt'], 'modo', m)
            
            context.bot_data['modo'] = modo

            logging.info("Se modificó el modo de operación del rele a: " + modo)

            await context.bot.send_message(update.message.chat.id, 
                                           text=f"El modo de operación del rele es: {modo}")
        else:
            await context.bot.send_message(update.message.chat.id, 
                                           text="El modo de operación debe ser 'manual' o 'automatico'")

async def rele(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /rele command by toggling the state of the relay."""

    logging.info("Se intenta de modificar el estado del rele")
    if context.bot_data.get('modo') == 1:
        await context.bot.send_message(update.message.chat.id,
                                       text="El modo de operación del rele es automático, no se puede cambiar el estado del rele")
    else:
        if 'rele' not in context.bot_data:
            await context.bot.send_message(update.message.chat.id,
                                           text="No se ha recibido la configuración del rele, por favor, inténtalo más tarde.")
            return
        
        await publicar_datos_mqtt(context.bot_data['mqtt'], 'rele', 'rele')

        context.bot_data['rele'] = 1 if context.bot_data['rele'] == 0 else 0
        logging.info("Se modificó el estado del rele a: " + str(context.bot_data['rele']))
        await context.bot.send_message(update.message.chat.id,
                                   text="El estado del rele de la Raspberry Pi Pico ha sido modificado")

async def destello(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /destello command by making an LED flash for a specified duration."""

    logging.info("Se intenta de hacer destellar un led")
    await publicar_datos_mqtt(context.bot_data['mqtt'], 'destello', 'destello')

    await context.bot.send_message(update.message.chat.id,
                                   text="El led de la Raspberry Pi Pico destellará por un tiempo determinado")

async def main():
    """Main function to set up the Telegram bot and its handlers."""
    
    mqtt_client = crear_cliente_mqtt()

    logging.info("Iniciando el Bot de Telegram")
    token=os.environ["TB_TOKEN"]
    autorizados=[int(x) for x in os.environ["TB_AUTORIZADOS"].split(',')] # Si no funciona, poner como global
    logging.info(autorizados)
    application = Application.builder().token(token).build()

    application.bot_data['mqtt'] = mqtt_client # Store the MQTT client in bot_data for later use
    
    asyncio.create_task(oyente_mqtt(application)) # Start the MQTT listener in the background

    # Set up command and message handlers
    application.add_handler(MessageHandler((~filters.User(autorizados)), sin_autorizacion))
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('acercade', acercade))
    application.add_handler(CommandHandler('config', config))
    application.add_handler(CommandHandler('periodo', periodo))
    application.add_handler(CommandHandler('setpoint', setpoint))
    application.add_handler(CommandHandler('modo', modo))
    application.add_handler(CommandHandler('rele', rele))
    application.add_handler(CommandHandler('destello', destello))
    application.add_handler(CommandHandler('temperatura_humedad', temperatura_humedad))
    
    await application.run_polling()

if __name__ == '__main__':
    nest_asyncio.apply()
    asyncio.run(main())