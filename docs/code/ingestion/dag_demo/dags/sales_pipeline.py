from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import json
import random
import os

DATA_DIR = "../airflow_demo"
os.makedirs(DATA_DIR, exist_ok=True)

# -------------------
# TASK 1: FETCH
# -------------------
def fetch():
    data = {"date": str(datetime.now().date()), "value": 100}
    
    with open(f"{DATA_DIR}/data.json", "w") as f:
        json.dump(data, f)
    
    print("Fetched data")

# -------------------
# TASK 2: TRANSFORM (with failure)
# -------------------
def transform():
    if random.random() < 0.5:
        raise Exception("Random failure in transform!")

    with open(f"{DATA_DIR}/data.json") as f:
        data = json.load(f)

    data["value"] *= 2

    with open(f"{DATA_DIR}/data_transformed.json", "w") as f:
        json.dump(data, f)

    print("Transformed data")

# -------------------
# TASK 3: LOAD (idempotent)
# -------------------
def load():
    with open(f"{DATA_DIR}/data_transformed.json") as f:
        data = json.load(f)

    db_file = f"{DATA_DIR}/db.txt"
    existing = set()

    if os.path.exists(db_file):
        with open(db_file) as f:
            for line in f:
                existing.add(eval(line)["date"])

    if data["date"] in existing:
        print("Skipping duplicate load")
    else:
        with open(db_file, "a") as f:
            f.write(str(data) + "\n")
        print("Loaded into DB")

# -------------------
# DAG DEFINITION
# -------------------
with DAG(
    dag_id="sales_pipeline_demo",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
) as dag:

    fetch_task = PythonOperator(
        task_id="fetch",
        python_callable=fetch
    )

    transform_task = PythonOperator(
        task_id="transform",
        python_callable=transform,
        retries=3
    )

    load_task = PythonOperator(
        task_id="load",
        python_callable=load
    )

    fetch_task >> transform_task >> load_task