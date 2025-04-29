import asyncio, ssl, certifi, logging, os
import aiomqtt

logging.basicConfig(format='%(asctime)s - cliente mqtt - %(levelname)s:%(message)s', level=logging.INFO, datefmt='%d/%m/%Y %H:%M:%S %z')

async def topic_consumer(queue, topic_name):
    logger = logging.getLogger(f"task-{topic_name}")
    logger.info(f"This task read {topic_name}")

    while True:
        message = await queue.get()
        logger.info(f"[{topic_name}] = {message.payload.decode()}")

async def distributor(client, topic_queues):
    logger = logging.getLogger("task-distributor")
    logger.info("This task distribute messages to queues")

    async for message in client.messages:
        for topic, queue in topic_queues.items():
            if message.topic.matches(topic):
                queue.put_nowait(message)
                break

async def increment_counter(db):    
    logger = logging.getLogger("task-counter")
    logger.info("This task increment the counter")
    
    while True:
        await asyncio.sleep(3)
        db['counter'] += 1
        logger.info(f"Counter: {db['counter']}")

async def publish(client, topic, db):
    logger = logging.getLogger("task-publish")
    logger.info("This task publish messages")

    while True:
        logger.info(f"Publishing to {topic}: {db['counter']}")
        await client.publish(topic, payload=str(db['counter']).encode('utf-8'))
        await asyncio.sleep(5)

async def main():
    tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    tls_context.verify_mode = ssl.CERT_REQUIRED
    tls_context.check_hostname = True
    tls_context.load_default_certs()

    topic_1 = os.environ['TOPICO_1']
    topic_2 = os.environ['TOPICO_2']
    publish_topic = os.environ['TOPICO']

    topic_queues = {
        topic_1: asyncio.Queue(),
        topic_2: asyncio.Queue()
    }

    db = {'counter': 0}


    async with aiomqtt.Client(
            os.environ['SERVIDOR'],
            port=8883,
            tls_context=tls_context,
    ) as client:
            await client.subscribe(os.environ['TOPICO_1'])  
            await client.subscribe(os.environ['TOPICO_2'])
            
            # Use a task group to manage and await all tasks
            async with asyncio.TaskGroup() as tg:
                tg.create_task(distributor(client, topic_queues))
                tg.create_task(topic_consumer(topic_queues[topic_1], topic_1))
                tg.create_task(topic_consumer(topic_queues[topic_2], topic_2))
                tg.create_task(increment_counter(db))
                tg.create_task(publish(client, publish_topic, db))


if __name__ == "__main__":
    try:
        logging.info(" ----- Iniciando cliente MQTT -----")
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info(" ----- Programa interrumpido por el usuario -----")
