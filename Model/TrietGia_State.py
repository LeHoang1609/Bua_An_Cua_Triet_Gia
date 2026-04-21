"""
philosopher_state.py - Trạng thái và thống kê của triết gia
"""

import time
from enum import Enum
from dataclasses import dataclass, field


class State(Enum):
    """Các trạng thái của triết gia"""
    THINKING = "thinking"
    HUNGRY   = "hungry"
    EATING   = "eating"
    WAITING  = "waiting"


class Solution(Enum):
    """Các giải pháp"""
    NAIVE               = "naive"
    RESOURCE_HIERARCHY  = "resource_hierarchy"
    ARBITRATOR          = "arbitrator"
    CHANDY_MISRA        = "chandy_misra"


@dataclass
class PhilosopherStats:
    """
    Thống kê của một triết gia
    """

    ma_triet_gia: int

    tong_so_lan_an:     int   = 0
    tong_thoi_gian_nghi: float = 0.0
    tong_thoi_gian_cho:  float = 0.0
    tong_thoi_gian_an:   float = 0.0

    so_lan_thoat_deadlock: int = 0
    so_lan_starvation:     int = 0

    _bat_dau_nghi: float = field(default=0.0, repr=False)
    _bat_dau_cho:  float = field(default=0.0, repr=False)
    _bat_dau_an:   float = field(default=0.0, repr=False)


    def bat_dau_nghi(self):
        self._bat_dau_nghi = time.monotonic()

    def bat_dau_cho(self):
        self._bat_dau_cho = time.monotonic()

    def bat_dau_an(self):
        hien_tai = time.monotonic()
        self._bat_dau_an = hien_tai

        if self._bat_dau_cho:
            self.tong_thoi_gian_cho += hien_tai - self._bat_dau_cho
            self._bat_dau_cho = 0.0


    def ket_thuc_nghi(self):
        if self._bat_dau_nghi:
            self.tong_thoi_gian_nghi += time.monotonic() - self._bat_dau_nghi
            self._bat_dau_nghi = 0.0

    def ket_thuc_an(self):
        if self._bat_dau_an:
            self.tong_thoi_gian_an += time.monotonic() - self._bat_dau_an
            self._bat_dau_an = 0.0

        self.tong_so_lan_an += 1


    def thoi_gian_cho_hien_tai(self) -> float:
        if self._bat_dau_cho:
            return time.monotonic() - self._bat_dau_cho
        return 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.ma_triet_gia,
            "tong_so_lan_an": self.tong_so_lan_an,
            "tong_thoi_gian_nghi": round(self.tong_thoi_gian_nghi, 2),
            "tong_thoi_gian_cho": round(self.tong_thoi_gian_cho, 2),
            "tong_thoi_gian_an": round(self.tong_thoi_gian_an, 2),
            "thoat_deadlock": self.so_lan_thoat_deadlock,
            "starvation": self.so_lan_starvation,
        }