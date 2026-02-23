
import json
import os
import threading
import time

class PersistentRedisMock:
    """
    A high-fidelity replacement for fakeredis that persists to disk.
    Fixes the 'transient state' simulation issue in the Nexus Bridge.
    """
    def __init__(self, filename="swarm_v2_artifacts/redis_state.json"):
        self.filename = filename
        self.data = {"strings": {}, "hashes": {}, "lists": {}}
        self.lock = threading.Lock()
        self._load()

    def _load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except:
                pass

    def _save(self):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def ping(self):
        return True

    def set(self, key, value):
        with self.lock:
            self.data["strings"][str(key)] = str(value)
            self._save()
        return True

    def get(self, key):
        with self.lock:
            val = self.data["strings"].get(str(key))
            return val.encode() if val else None

    def hset(self, name, key=None, value=None, mapping=None):
        with self.lock:
            if name not in self.data["hashes"]:
                self.data["hashes"][name] = {}
            
            if mapping:
                for k, v in mapping.items():
                    self.data["hashes"][name][str(k)] = str(v)
            else:
                self.data["hashes"][name][str(key)] = str(value)
            self._save()
        return 1

    def hgetall(self, name):
        with self.lock:
            val = self.data["hashes"].get(name, {})
            # Return bytes-encoded dict for compatibility with redis-py
            return {k.encode(): v.encode() for k, v in val.items()}

    def rpush(self, name, value):
        with self.lock:
            if name not in self.data["lists"]:
                self.data["lists"][name] = []
            self.data["lists"][name].append(str(value))
            self._save()
        return len(self.data["lists"][name])

    def blpop(self, keys, timeout=0):
        if isinstance(keys, str):
            keys = [keys]
        
        start_time = time.time()
        while True:
            with self.lock:
                for key in keys:
                    if key in self.data["lists"] and self.data["lists"][key]:
                        val = self.data["lists"][key].pop(0)
                        self._save()
                        return (key.encode(), val.encode())
            
            if timeout > 0 and (time.time() - start_time) > timeout:
                return None
            
            time.sleep(0.1)
