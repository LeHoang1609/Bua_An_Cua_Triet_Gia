import threading

class Fork:
    

    def __init__(self, fork_id: int):
        self.fork_id = fork_id
        self._lock = threading.Lock()
        self.held_by: int | None = None
        self.dirty: bool = True         
    def acquire(self, timeout: float | None = None) -> bool:
        if timeout is None:
            self._lock.acquire()
            return True
        return self._lock.acquire(timeout=timeout)

    def release(self):
        """Thả fork, xóa thông tin người giữ."""
        self.held_by = None
        self._lock.release()

    @property
    def is_held(self) -> bool:
        return self.held_by is not None

    def __repr__(self):
        state = f"held by P{self.held_by}" if self.is_held else "free"
        return f"Fork(id={self.fork_id}, {state}, dirty={self.dirty})"


        âsdasd