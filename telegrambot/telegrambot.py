from telegram.ext import Application, CommandHandler, MessageHandler, filters
import logging, os, asyncio
import nest_asyncio
from comandhandlers import (
    start, acercade, config, periodo, setpoint, modo, destello, sin_autorizacion, crear_cliente_mqtt, oyente_mqtt, temperatura_humedad, rele
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.basicConfig(format='%(asctime)s - TelegramBot - %(levelname)s - %(message)s', level=logging.INFO) 

async def main():
    """Main function to set up the Telegram bot and its handlers."""
    
    mqtt_client = crear_cliente_mqtt()

    logging.info("Iniciando el Bot de Telegram")
    token=os.environ["TB_TOKEN"]
    autorizados=[int(x) for x in os.environ["TB_AUTORIZADOS"].split(',')] # Si no funciona, por como global
    logging.info(autorizados)
    application = Application.builder().token(token).build()

    application.bot_data['mqtt'] = mqtt_client
    
    asyncio.create_task(oyente_mqtt(application))

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