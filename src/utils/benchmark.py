import time
import utils.logger as logging

class TimeStamp:
    def __init__():
        self.start_time = time.time()
        self.end_time = time.time()
        self.benchmark = 0

    def __str__(self):
        return f"benchmark: {self.benchmark:.5f} ms"

    def stamping(self):
        self.end_time = time.time()
        self.benchmark = self.end_time - self.start_time
        self.start_time = self.end_time