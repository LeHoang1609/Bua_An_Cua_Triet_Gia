import threading
import time
import random

class Fork:
    def __init__(self, fork_id):
        self.fork_id = fork_id
        self.lock = threading.Lock()

class Philosopher(threading.Thread):
    def __init__(self, phil_id, left_fork, right_fork, controller_callback):
        super().__init__()
        self.phil_id = phil_id
        self.left_fork = left_fork
        self.right_fork = right_fork
        self.callback = controller_callback
        self.daemon = True 

    def run(self):
        while True:
            # 1. Trạng thái Suy nghĩ
            self.callback(self.phil_id, "THINKING")
            time.sleep(random.uniform(1, 3))

            # 2. Trạng thái Đói
            self.callback(self.phil_id, "HUNGRY")

            # 3. Thuật toán lấy đũa (Asymmetric - Tránh Deadlock)
            if self.phil_id % 2 == 0:
                first, second = self.right_fork, self.left_fork
            else:
                first, second = self.left_fork, self.right_fork

            with first.lock:
                with second.lock:
                    # 4. Trạng thái Ăn
                    self.callback(self.phil_id, "EATING")
                    time.sleep(random.uniform(1, 2))