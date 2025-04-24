import asyncio, ssl, certifi, logging, os
import aiomqtt

logging.basicConfig(format='%(asctime)s - cliente mqtt - %(levelname)s:%(message)s', level=logging.INFO, datefmt='%d/%m/%Y %H:%M:%S %z')

async def topic_1_consumer():
    logger = logging.getLogger(f"task-TOPICO_1")
    logger.info("This task read TOPICO_1")
    while True:
        message = await topic_1_queue.get()
        print(f"[TOPICO_1/#] = {message.payload}")
        
async def topic_2_consumer():
    logger = logging.getLogger(f"task-TOPICO_2")
    logger.info("This task read TOPICO_2")
    while True:
        message = await topic_2_queue.get()
        print(f"[TOPICO_2/#] = {message.payload}")

topic_1_queue = asyncio.Queue()
topic_2_queue = asyncio.Queue()

async def distributor(client):
    # Sort messages into the appropriate queues
    async for message in client.messages:
        if message.topic.matches(os.environ['TOPICO_1']):
            topic_1_queue.put_nowait(message)
        elif message.topic.matches(os.environ['TOPICO_2']):
            topic_2_queue.put_nowait(message)

async def increment_counter(db):
    logger = logging.getLogger("task-counter")
    logger.info("This task increment the counter")
    
    while True:
        await asyncio.sleep(3)
        db['counter'] += 1
        logger.info(f"Counter: {db['counter']}")

async def publish(client, topic, payload):
    logger = logging.getLogger("task-publish")
    while True:
        logger.info(f"Publishing to {topic}: {payload}")
        await client.publish(topic, payload=str(payload).encode('utf-8'))
        await asyncio.sleep(5)

async def main():
    tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    tls_context.verify_mode = ssl.CERT_REQUIRED
    tls_context.check_hostname = True
    tls_context.load_default_certs()

    async with aiomqtt.Client(
        os.environ['SERVIDOR'],
        port=8883,
        tls_context=tls_context,
    ) as client:
        db = {}
        db['counter'] = 0

        await client.subscribe(os.environ['TOPICO_1'])
        await client.subscribe(os.environ['TOPICO_2'])
        
        # Use a task group to manage and await all tasks
        async with asyncio.TaskGroup() as tg:
            tg.create_task(distributor(client))
            tg.create_task(topic_1_consumer())
            tg.create_task(topic_2_consumer())
            tg.create_task(increment_counter(db))
            tg.create_task(publish(client, os.environ['TOPICO'], db['counter']))

if __name__ == "__main__":
    asyncio.run(main())

"""
Publish

async with Client("test.mosquitto.org") as client:
    await client.publish("temperature/outside", payload=28.4)

async def publish
Subscribe

async with Client("test.mosquitto.org") as client:
    await client.subscribe("temperature/#")
    async for message in client.messages:
        print(message.payload)

        

recibe por variables de entorno un tópico en el cuál publica cada 5 segundos el estado de un contador.
el contador se incrementa cada 3 segundos en una corrutina (task) diferente.
no utilizar variables globales.
utilizar aiomqtt.
crear un solo objeto client.
capturar la excepción al detener con ctrl-c.
se crea el contenedor con docker compose
"""