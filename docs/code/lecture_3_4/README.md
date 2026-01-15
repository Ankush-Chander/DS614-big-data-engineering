# Log based storage engine
This is a simple log based storage engine implementation using FastAPI

Source : [log_based_storage_engine](./log_based_main.py)

## Setup

```bash
pip install -r requirements.txt
```

## Run
```bash
uvicorn log_based_main:app --reload
```


## API

```bash
# set key
curl -X POST http://localhost:8000/set_db  -H 'accept: application/json'   -H 'Content-Type: application/json'  --data '{"key":"42","val":"life"}'

# get key
curl -X GET http://localhost:8000/get_db/42
# returns `life`

# update key
curl -X POST http://localhost:8000/set_db  -H 'accept: application/json'   -H 'Content-Type: application/json'  --data '{"key":"42","val":"answer to life"}'

# get key
curl -X GET http://localhost:8000/get_db/42
# returns `answer to life`

# inspect database
cat database.csv
```

