## Airflow Demo

### Setup

```bash
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.8.1/docker-compose.yaml'
docker compose up

# set AIRFLOW_UID
```bash
export AIRFLOW_UID=$(id -u)
```

### create dag folder

```bash
mkdir -p dags
```
