from fastapi import FastAPI
from pydantic import BaseModel
import struct
import os
import threading
from contextlib import contextmanager
import psutil

# ----------------------------
# Read–Write Lock
# ----------------------------

class ReadWriteLock:
    def __init__(self):
        self._users = 0
        self._maintainance = False # variable that tracks if the system is in maintainance mode
        self._monitor = threading.Lock() # lock that protects the above variables
        self._users_ok = threading.Condition(self._monitor) # condition variable that is signalled when users are acceptable
        self._maintainance_ok = threading.Condition(self._monitor) # condition variable that is signalled when the maintainance mode is acceptable

    @contextmanager
    def access_lock(self):      # access_lock()
        with self._monitor:
            while self._maintainance:
                self._users_ok.wait()
            self._users += 1
        try:
            yield
        finally:
            with self._monitor:
                self._users -= 1
                if self._users == 0:
                    self._maintainance_ok.notify()

    @contextmanager
    def maintenance_lock(self):     # maintenance_lock()
        with self._monitor:
            while self._maintainance or self._users > 0:
                self._maintainance_ok.wait()
            self._maintainance = True
        try:
            yield
        finally:
            with self._monitor:
                self._maintainance = False
                self._maintainance_ok.notify()
                self._users_ok.notify_all()


# ----------------------------
# Locks (minimal set)
# ----------------------------

rw_lock = ReadWriteLock()          # access_lock / maintenance_lock

append_lock = threading.Lock()    # serializes file appends
index_lock = threading.Lock()     # protects in-memory index

# ----------------------------
# App & State
# ----------------------------

app = FastAPI()

DATA_FILE = "database.bin"
TMP_FILE = "database_compact.bin"
TOMBSTONE = "__TOMBSTONE__"

KEY_OFFSET_MAP = {}


# ----------------------------
# Helpers
# ----------------------------

class Item(BaseModel):
    key: str
    val: str


def write_record(fp, key: str, val: str) -> int:
    position = fp.tell()
    print(f"process:{os.getpid()}, thread: {threading.current_thread().ident} running on CPU core#{psutil.Process().cpu_num()} read offset:{position}")

    key_b = key.encode("utf-8")
    val_b = val.encode("utf-8")
    header = struct.pack("II", len(key_b), len(val_b))
    fp.write(header)
    fp.write(key_b)
    fp.write(val_b)
    return position


# ----------------------------
# API Endpoints
# ----------------------------

@app.post("/set_db")
def set_db(item: Item):
    # access_lock(): normal operation
    with rw_lock.access_lock():
      with append_lock:
        with open(DATA_FILE, "ab") as fp:
          position = write_record(fp, item.key, item.val)
        # atomic metadata update
        with index_lock:
          KEY_OFFSET_MAP[item.key] = position

    print(f"process:{os.getpid()}, thread: {threading.current_thread().ident} running on CPU core#{psutil.Process().cpu_num()} => {KEY_OFFSET_MAP}")
    return {"message": "value set"}


@app.get("/get_db/{key}")
def get_db(key: str):
    # access_lock(): normal operation
    with rw_lock.access_lock():
      with index_lock:
        position = KEY_OFFSET_MAP.get(key)

      if position is None:
        return "undefined"

      with open(DATA_FILE, "rb") as fp:
        fp.seek(position)
        header = fp.read(8)
        key_len, val_len = struct.unpack("II", header)
        _ = fp.read(key_len)              # key
        val = fp.read(val_len).decode("utf-8")

      if val == TOMBSTONE:
        return "undefined"

      return val


@app.delete("/delete_db/{key}")
def delete_db(key: str):
    # access_lock(): normal operation
    with rw_lock.access_lock():
      with open(DATA_FILE, "ab") as fp:
        position = write_record(fp, key, TOMBSTONE)

      with index_lock:
        KEY_OFFSET_MAP[key] = position

    return {"message": "value deleted"}


@app.post("/compact_db")
def compact_db():
    # maintenance_lock(): exclusive stop-the-world
    with rw_lock.maintenance_lock():
        new_index = {}
        import time
        time.sleep(20)
        with open(DATA_FILE, "rb") as src, open(TMP_FILE, "wb") as dst:
            while True:
                header = src.read(8)
                if not header:
                    break

                key_len, val_len = struct.unpack("II", header)
                key = src.read(key_len).decode("utf-8")
                val = src.read(val_len).decode("utf-8")

                with index_lock:
                    latest_offset = KEY_OFFSET_MAP.get(key)

                record_start = src.tell() - (8 + key_len + val_len)

                if record_start == latest_offset and val != TOMBSTONE:
                    new_pos = write_record(dst, key, val)
                    new_index[key] = new_pos

        os.replace(TMP_FILE, DATA_FILE)

        with index_lock:
            KEY_OFFSET_MAP.clear()
            KEY_OFFSET_MAP.update(new_index)

    return {"message": "compacted"}
