from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import struct
import os

app = FastAPI()

"""
1. How do we avoid full file read? 
via in-memory hash map.

2. How do we handle deletion? 
via tombstones.

3. How do we handle the ever growing file?
via compaction

4. ***How do we optimize dataset format?***
5. How do we handle larger than main memory dataset?
6. How do we handle service restart/crash?
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
    with open("database.bin", "ab") as fp:
      position = fp.tell()
      
      key = item.key.encode("utf-8")
      val = item.val.encode("utf-8")

      header = struct.pack("II", len(key), len(val))
      fp.write(header) # TypeError: write() argument must be str, not bytes
           
      fp.write(key)
      fp.write(val)

      KEY_OFFSET_MAP[item.key] = position
      print(KEY_OFFSET_MAP)
    return {"message": "value set"}



@app.get("/get_db/{key}")
async def get_db(key):
    vals = []
    with open("database.bin", "rb") as fp:
      position = KEY_OFFSET_MAP.get(key, None)
      if not position:
        return "undefined"
      
      fp.seek(position)
      header = fp.read(8)
      key_len,val_len  = struct.unpack("II", header)
      
      # read bytes
      key = fp.read(key_len)
      val = fp.read(val_len)

      # decode val
      val = val.decode("utf-8")

      if val =="_TOMBSTONE__":
        return "undefined"
      
      return val


@app.delete("/delete_db/{key}")
async def delete(key):
  with open("database.bin", "a") as fp:
      position = fp.tell()
      fp.write(f"{key},__TOMBSTONE__\n")
      KEY_OFFSET_MAP[key] = position
  return {"message": "value deleted"}    


@app.get("/compact_db")
async def compact():
  """
  remove tombstones and remove duplicates
  """
  with open("database.bin", "rb") as fp:
    with open("database_compact.bin", "wb") as fp2:
      while(True):
        header = fp.read(8)
        if not header:
          break
        key_len,val_len  = struct.unpack("II", header)
        
        # read bytes
        key = fp.read(key_len).decode("utf-8")
        val = fp.read(val_len).decode("utf-8")

        if fp.tell() == KEY_OFFSET_MAP.get(key, None) and val != "__TOMBSTONE__":
          KEY_OFFSET_MAP[key] = fp2.tell()
          fp2.write(header)
          fp2.write(key.encode("utf-8"))
          fp2.write(val.encode("utf-8"))
        
  os.remove("database.bin")
  os.rename("database_compact.bin", "database.bin")

  print(KEY_OFFSET_MAP)        
  return {"message": "compacted"}
