from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import logging, os, asyncio, traceback, locale, ssl
from aiomqtt import Client
import nest_asyncio

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.basicConfig(format='%(asctime)s - TelegramBot - %(levelname)s - %(message)s', level=logging.INFO) 

def crear_cliente_mqtt():
    """Returns:
            Client: A Mqtt client configured to connect to the server specified by the environment variables."""
    
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
    kb = [["temperatura"],["humedad"],["gráfico temperatura"],["gráfico humedad"]]
    await context.bot.send_message(update.message.chat.id, 
                                   text="Bienvenido al Bot "+ nombre + " " + apellido + 
                                   '\n Utiliza el comando "acercade" para más información de como usar el Bot'
                                   + '\nUtiliza el comando "config" para obtemer la configuración de la Raspberry Pi Pico',
                                   reply_markup=ReplyKeyboardMarkup(kb))

async def acercade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /acercade command by providing information about the bot and its commands."""
    
    logging.info("se solicitó información del Bot")
    await context.bot.send_message(update.message.chat.id, 
                                   text="Comandos que tiene el Bot:\n" +
                                        "Comando                    -   Descripción\n" +
                                        "/periodo <tiempo>          -   Tiempo de sensado de datos\n" +
                                        "/setpoint <temperatura>    -   Si es superada esta temperatura se activa el Rele\n" +
                                        "\nAdemás puedes utilizar el teclado virtual para:\n" +
                                        "mediciones                -   Te muestra la última temperatura y humedad registrada\n" +
                                        "rele                       -   Enciende o apaga el rele\n" +
                                        "destello                   -   Destella un led por un tiempo\n" +
                                        "modo                       -   Cambia el modo de operación del rele\n")

async def config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /config command by providing the current configuration of the Raspberry Pi Pico."""

    logging.info("se solicitó la configuración de la Raspberry Pi Pico")
    await context.bot.send_message(update.message.chat.id, 
                                   text="La configuración de la Raspberry Pi Pico es:\n" +
                                        "Nombre del dispositivo: " + os.environ["NOMBRE_DISPOSITIVO"] + 
                                        "\nEl modo del Rele es:" + os.environ["MODO_RELE"] +
                                        "\nEl tiempo de encendido del rele es:" + os.environ["TIEMPO_RELE"] +
                                        "\nEl modo de operación del rele es:" + os.environ["MODO_OPERACION"] +
                                        "\nEl setpoint de temperatura es:" + os.environ["SETPOINT_TEMPERATURA"])

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

async def main():
    """Main function to set up the Telegram bot and its handlers."""
    
    mqtt_client = crear_cliente_mqtt()

    logging.info("Iniciando el Bot de Telegram")
    token=os.environ["TB_TOKEN"]
    autorizados=[int(x) for x in os.environ["TB_AUTORIZADOS"].split(',')] # Si no funciona, por como global
    logging.info(autorizados)
    application = Application.builder().token(token).build()

    application.bot_data['mqtt'] = mqtt_client

    application.add_handler(MessageHandler((~filters.User(autorizados)), sin_autorizacion))
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('acercade', acercade))
    application.add_handler(CommandHandler('config', config))
    application.add_handler(CommandHandler('periodo', periodo))
    application.add_handler(CommandHandler('setpoint', setpoint))
    await application.run_polling()

if __name__ == '__main__':
    nest_asyncio.apply()
    asyncio.run(main())