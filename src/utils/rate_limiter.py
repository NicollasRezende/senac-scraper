import time
import threading

class RateLimiter:
    def __init__(self, delay: float):
        self.delay = delay
        self.last_request = 0
        self.lock = threading.Lock()
    
    def wait(self):
        with self.lock:
            now = time.time()
            elapsed = now - self.last_request
            if elapsed < self.delay:
                time.sleep(self.delay - elapsed)
            self.last_request = time.time()