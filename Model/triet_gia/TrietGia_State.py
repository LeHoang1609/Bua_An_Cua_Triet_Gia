from enum import Enum


class TrangThai(Enum):
    DANG_NGHI   = "Suy nghĩ"
    DANG_DOI    = "Chờ đũa"
    DANG_AN     = "Đang ăn"
    BI_DEADLOCK = "Deadlock"


class GiaiPhap(Enum):
    NAIVE      = "naive"
    SEMAPHORE  = "semaphore"
    MONITOR    = "monitor"       # ← MỚI: Monitor thực sự với Condition Variable
    THU_TU_DUA = "thu_tu_dua"