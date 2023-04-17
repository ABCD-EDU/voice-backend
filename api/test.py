from fastapi import APIRouter, HTTPException

import util.db.client as db
import util.kafka.producer as prod
import util.kafka.consumer as cons

router = APIRouter()


@router.get("/mysql")
async def test():
    try:
        cursor = db.get_db().cursor()
        cursor.execute("select @@version")
        version = cursor.fetchone()

        if version:
            print('Running version: ', version)
        else:
            print('Not connected.')
    except:
        raise HTTPException(
            status_code=500, detail="Something went wrong with MYSQL")


@router.get("/producer")
async def producer():
    try:
        producer = prod.KafkaProducerSingleton().getInstance().producer

        producer.send('test', key=b'foo', value=b'bar')
        return {"message": "SENT", "key": "foo", "value": "bar"}
    except:
        raise HTTPException(
            status_code=500, detail="Something went wrong with Kafka Producer")


@router.get("/consumer")
async def consumer():
    # This request locks up the thread
    try:
        msgs = []
        print("test")
        consumer = cons.SingletonKafkaConsumer("test")
        print("consuming")

        for msg in consumer.consume():
            print(msg)
            msgs.append(msg)

        return msgs
    except:
        raise HTTPException(
            status_code=500, detail="Something went wrong with Kafka Consumer")
