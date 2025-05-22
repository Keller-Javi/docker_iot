from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import logging, os, asyncio, aiomysql, traceback, locale
import matplotlib.pyplot as plt
from io import BytesIO


token=os.environ["TB_TOKEN"]
autorizados=[int(x) for x in os.environ["TB_AUTORIZADOS"].split(',')]
logging.getLogger("httpx").setLevel(logging.WARNING)

logging.basicConfig(format='%(asctime)s - TelegramBot - %(levelname)s - %(message)s', level=logging.INFO)

async def sin_autorizacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("intento de conexión de: " + str(update.message.from_user.id))
    logging.info(context)
    logging.info(context.application)
    logging.info(context.application.handlers)
    logging.info(context.application.handlers[0])
    logging.info(context.application.handlers[0][0])
    logging.info(context.application.handlers[0][0].filters)
    logging.info(context.application.handlers[0][0].filters.invfilters)
    logging.info(context.application.handlers[0][0].filters.invfilters[0]) 
    # Pedir a chat que significa toda esta información que el bot de telegram le saca de los usuarios no autorizados
    # Se puede cambiar de manera dinámica los usuarios autorizados

    await context.bot.send_message(chat_id=update.effective_chat.id, text="no autorizado")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("se conectó: " + str(update.message.from_user.id))
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

async def acercade(update: Update, context):
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

async def config(update: Update, context):
    await context.bot.send_message(update.message.chat.id, 
                                   text="La configuración de la Raspberry Pi Pico es:\n" +
                                        "Nombre del dispositivo: " + os.environ["NOMBRE_DISPOSITIVO"] + 
                                        "\nEl modo del Rele es:" + os.environ["MODO_RELE"] +
                                        "\nEl tiempo de encendido del rele es:" + os.environ["TIEMPO_RELE"] +
                                        "\nEl modo de operación del rele es:" + os.environ["MODO_OPERACION"] +
                                        "\nEl setpoint de temperatura es:" + os.environ["SETPOINT_TEMPERATURA"])

async def periodo(update: Update, context):
    logging.info(context.args)
    if context.args:
        try:
            periodo=int(context.args[0])
            if periodo>0:
                await context.bot.send_message(update.message.chat.id, 
                                               text="El periodo de sensado es: " + str(periodo) + " segundos")
                #objeto.periodo=periodo
                #await context.bot.send_message(update.message.chat.id, 
                #                               text="El periodo de sensado es: " + str(objeto.periodo) + " segundos")
            else:
                await context.bot.send_message(update.message.chat.id, 
                                               text="El periodo de sensado debe ser mayor a 0")
        except ValueError:
            await context.bot.send_message(update.message.chat.id, 
                                           text="El periodo de sensado debe ser un número entero")

def main():
    logging.info(autorizados)
    application = Application.builder().token(token).build()
    application.add_handler(MessageHandler((~filters.User(autorizados)), sin_autorizacion))
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('acercade', acercade))
    application.add_handler(CommandHandler('config', config))
    application.run_polling()
    #application.bot_data['objeto] = objeto

if __name__ == '__main__':
    main()