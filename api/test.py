from fastapi import APIRouter, HTTPException
from airflow.api.client.local_client import Client
from datetime import datetime
import requests

import util.db.client as db
import util.kafka.producer as prod
import util.kafka.consumer as cons

router = APIRouter()

@router.post("/trigger_dag")
async def trigger_dag(dag_id: str, job: str):
    """
    Triggers an Airflow DAG with the specified dag_id and configuration parameters in conf.
    """
    airflow_url = "http://localhost:8080/api/v1"
    dag_run_url = f"{airflow_url}/dags/{dag_id}/dagRuns"
    headers = {"Content-Type": "application/json", "Authorization": "Basic YWlyZmxvdzphaXJmbG93"}
    payload = {"conf": {
        "id": job
    }}

    response = requests.post(dag_run_url, json=payload, headers=headers)
    response.raise_for_status()

    return {"message": "DAG triggered successfully!"}

@router.get("/check-dag")
async def dag(id: str):
    # Define the client object to connect to the Airflow server
    client = Client(None, None)

    # Define the execution date for the task
    execution_date = datetime.now()

    task_params = {
        "my_id": id
    }

    # Trigger the task using the client object
    client.trigger_dag(dag_id="my_fastapi_dag", run_id="test", conf=task_params)

    # Return a message indicating that the task has been triggered
    return {"message": f"Task call_fastapi_endpoint in DAG my_fastapi_dag has been triggered!"}

@router.get("/health-check")
async def check():
    return "Hello World"

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
