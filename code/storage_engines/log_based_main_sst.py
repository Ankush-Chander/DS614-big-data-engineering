from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import struct
import os
import threading
import psutil

app = FastAPI()

"""
1. How do we handle Out of memory?
2. How do we handle range queries?
2. How do we handle service restart/crash?
"""
# hashmap with O(1) key lookup
KEY_OFFSET_MAP = {}

SEGMENT_ID = 0
FLUSH_THRESHOLD = 4

mem_table = []  # supposed to be tree 



@app.get("/")
async def root():
    return {"message": "Hello World"}


class Item(BaseModel):
  key: str
  val: str

def write_record(fp, key, val):
  position = fp.tell()
  print(f"process:{os.getpid()}, thread: {threading.current_thread().ident} running on CPU core: {psutil.Process().cpu_num()} read offset:{position}")
  header = struct.pack("II", len(key), len(val))
  fp.write(header)
  key_bytes = key.encode("utf-8")
  val_bytes = val.encode("utf-8")
  fp.write(key_bytes)
  fp.write(val_bytes)
  return position


def flush(mem_table):
  global SEGMENT_ID
  print(f"flushing {len(mem_table)} records to segment {SEGMENT_ID}")
  next_segment = f"segment_{SEGMENT_ID}" 
  with open(next_segment, "ab" ) as fp:
    # expensive work around
    mem_table = sorted(mem_table, key=lambda x: x[0])
    for key, val in mem_table:
      position = write_record(fp, key, val)
  

@app.post("/set_db")
def set_db(item:Item):
    global SEGMENT_ID
    mem_table.append((item.key, item.val))
    if len(mem_table) >= FLUSH_THRESHOLD:
      flush(mem_table)
      mem_table.clear()
      SEGMENT_ID = SEGMENT_ID + 1
    return {"message": "value set"}



@app.get("/get_db/{key}")
async def get_db(key):
    vals = []
    with open("segment_0", "rb") as fp:
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
    with open("database.bin", "ab") as fp:
        position = write_record(fp, key, "__TOMBSTONE__")
        
    KEY_OFFSET_MAP[key] = position
    return {"message": "value deleted"}    


@app.get("/compact_db")
def compact():
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
          position = write_record(fp2, key, val)
          KEY_OFFSET_MAP[key] = position
        
  os.remove("database.bin")
  os.rename("database_compact.bin", "database.bin")

  print(KEY_OFFSET_MAP)        
  return {"message": "compacted"}
