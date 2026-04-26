

import threading


class ChiecDua:

    def __init__(self, ma_dua: int):
        self.ma_dua   = ma_dua
        self._lock    = threading.Lock()
        self.dang_giu: int | None = None   # ai đang cầm đũa này

    # ── Thao tác cầm / thả ───────────────────────────────────────────────

    def cam(self, timeout: float | None = None) -> bool:
        
        if timeout is None:
            self._lock.acquire()
            return True
        return self._lock.acquire(timeout=timeout)

    def tha(self):
        self.dang_giu = None
        self._lock.release()


    @property
    def dang_roi(self) -> bool:
        """True nếu đũa chưa có ai cầm."""
        return self.dang_giu is None

    def __repr__(self):
        trang_thai = f"P{self.dang_giu} đang cầm" if not self.dang_roi else "rảnh"
        return f"ChiecDua(ma={self.ma_dua}, {trang_thai})"