from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


class Item(BaseModel):
  key: str
  val: str

@app.post("/set_db")
async def set_db(item:Item):
    with open("database.csv", "a") as fp:
      fp.write(f"{item.key},{item.val}\n")

    return {"message": "value set"}



@app.get("/get_db/{key}")
async def get_db(key):
    vals = []
    with open("database.csv", "r") as fp:
      for line in fp:
        if line.startswith(f"{key},"):
          vals.append(line.replace(f"{key},",""))
      return vals[-1] if vals else "undefined"
