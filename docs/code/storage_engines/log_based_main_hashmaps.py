from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd

app = FastAPI()

"""
1. How do we avoid full file read? 
via in-memory hash map.

2. How do we handle deletion? 
via tombstones.

3. How do we handle the ever growing file?
via compaction

4. How do we optimize dataset format?
5. How do we handle concurrency?
6. How do we handle larger than main memory dataset?
7. How do we handle service restart/crash?
"""
# hashmap with O(1) key lookup
KEY_OFFSET_MAP = {}


@app.get("/")
async def root():
    return {"message": "Hello World"}


class Item(BaseModel):
  key: str
  val: str

@app.post("/set_db")
async def set_db(item:Item):
    with open("database.csv", "a") as fp:
      position = fp.tell()
      fp.write(f"{item.key},{item.val}\n")
      KEY_OFFSET_MAP[item.key] = position
      print(KEY_OFFSET_MAP)
    return {"message": "value set"}



@app.get("/get_db/{key}")
async def get_db(key):
    vals = []
    with open("database.csv", "r") as fp:
      position = KEY_OFFSET_MAP.get(key, None)
      if not position:
        return "undefined"
      fp.seek(position)
      for line in fp:
        if line.startswith(f"{key},"):
          vals.append(line.strip().replace(f"{key},",""))
      val = vals[-1] if vals else "undefined"
      if val == "__TOMBSTONE__":
        return "undefined"
      return val


@app.delete("/delete_db/{key}")
async def delete(key):
  with open("database.csv", "a") as fp:
      position = fp.tell()
      fp.write(f"{key},__TOMBSTONE__\n")
      KEY_OFFSET_MAP[key] = position
  return {"message": "value deleted"}    


@app.get("/compact_db")
async def compact():
  """
  remove tombstones and remove duplicates
  """
  database_df = pd.read_csv("database.csv", header=None, names=["key", "val"])
  database_df.drop_duplicates(subset="key", keep="last", inplace=True)
  database_df = database_df[database_df["val"] != "__TOMBSTONE__"]
  database_df.to_csv("database.csv", index=False, header=False)
  KEY_OFFSET_MAP.clear()

  byte_offset = 0
  for i, row in database_df.iterrows():
    KEY_OFFSET_MAP[row["key"]] = byte_offset
    byte_offset += len(row["key"]) + len(row["val"]) + 2
 
    
  return {"message": "compacted"}
