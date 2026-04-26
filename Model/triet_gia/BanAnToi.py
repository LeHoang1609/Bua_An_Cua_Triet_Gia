import threading
import time
import logging
from typing import Callable

from .ChiecDua import ChiecDua
from .TrietGia import TrietGia
from .TrietGia_State import TrangThai, GiaiPhap

logger = logging.getLogger(__name__)


class BanAnToi:
    SO_MIN = 3
    SO_MAX = 8

    def __init__(
        self,
        so_triet_gia: int = 5,
        giai_phap: GiaiPhap = GiaiPhap.NAIVE,
        toc_do: float = 1.0,
    ):
        if not (self.SO_MIN <= so_triet_gia <= self.SO_MAX):
            raise ValueError(f"so_triet_gia phải từ {self.SO_MIN} đến {self.SO_MAX}")

        self.so_triet_gia = so_triet_gia
        self.giai_phap    = giai_phap
        self.toc_do       = toc_do

        self.dua: list[ChiecDua] = [
            ChiecDua(i) for i in range(so_triet_gia)
        ]

        # Semaphore: tối đa N-1 người được ngồi cùng lúc
        self.quan_gia = threading.Semaphore(so_triet_gia - 1)

        # Monitor: Condition Variable dùng chung cho tất cả triết gia
        self.monitor_condition = threading.Condition(threading.Lock())

        self.triet_gia: list[TrietGia] = [
            TrietGia(i, self, giai_phap) for i in range(so_triet_gia)
        ]

        self.dang_chay     = False
        self.dang_tam_dung = False
        self.thoi_gian_bat_dau: float | None = None

        self.so_deadlock = 0

        self._callback_thay_doi: Callable | None = None

    def bat_dau(self):
        if self.dang_chay:
            logger.warning("Simulation đang chạy, bỏ qua lệnh bat_dau.")
            return

        self.dang_chay         = True
        self.dang_tam_dung     = False
        self.thoi_gian_bat_dau = time.monotonic()

        for tg in self.triet_gia:
            tg.start()

        logger.info(
            f"BanAnToi bắt đầu: {self.so_triet_gia} triết gia, "
            f"giải pháp = {self.giai_phap.value}"
        )

    def dung(self):
        if not self.dang_chay:
            return

        self.dang_chay     = False
        self.dang_tam_dung = False

        for tg in self.triet_gia:
            tg.dung()

        # Notify monitor condition để các thread đang wait() thoát ra
        if self.giai_phap == GiaiPhap.MONITOR:
            with self.monitor_condition:
                self.monitor_condition.notify_all()

        logger.info("BanAnToi đã dừng.")

    def tam_dung(self):
        self.dang_tam_dung = True
        logger.info("BanAnToi tạm dừng.")

    def tiep_tuc(self):
        self.dang_tam_dung = False
        logger.info("BanAnToi tiếp tục.")

    def dat_lai(self, so_triet_gia: int = None, giai_phap: GiaiPhap = None):
        self.dung()
        n  = so_triet_gia or self.so_triet_gia
        gp = giai_phap    or self.giai_phap
        self.__init__(n, gp, self.toc_do)
        logger.info(f"Đặt lại: {n} triết gia, giải pháp = {gp.value}")

    def dat_toc_do(self, toc_do: float):
        if toc_do <= 0:
            raise ValueError("toc_do phải > 0")
        self.toc_do = toc_do

    def dang_ky_thay_doi(self, callback: Callable):
        self._callback_thay_doi = callback

    def thong_bao_thay_doi(self):
        if self._callback_thay_doi:
            try:
                self._callback_thay_doi()
            except Exception as e:
                logger.error(f"Lỗi callback: {e}")

    def lay_snapshot(self) -> dict:
        da_chay = self.thoi_gian_bat_dau is not None
        thoi_gian_chay = (
            round(time.monotonic() - self.thoi_gian_bat_dau, 1)
            if da_chay else 0.0
        )

        return {
            "so_triet_gia":   self.so_triet_gia,
            "giai_phap":      self.giai_phap.value,
            "dang_chay":      self.dang_chay,
            "dang_tam_dung":  self.dang_tam_dung,
            "toc_do":         self.toc_do,
            "thoi_gian_chay": thoi_gian_chay,
            "so_deadlock":    self.so_deadlock,
            "triet_gia": [
                tg.lay_thong_ke() for tg in self.triet_gia
            ],
            "triet_gia_cho_hien_tai": [
                tg.lay_thoi_gian_cho_hien_tai() for tg in self.triet_gia
            ],
            "dua": [
                {
                    "ma":       d.ma_dua,
                    "dang_roi": d.dang_roi,
                    "dang_giu": d.dang_giu,
                }
                for d in self.dua
            ],
        }

    def lay_thong_ke_tong(self) -> dict:
        so_bua        = [tg.so_bua_an for tg in self.triet_gia]
        thoi_gian_cho = [tg.tong_thoi_gian_cho for tg in self.triet_gia]
        tong_bua      = sum(so_bua)

        return {
            "giai_phap":      self.giai_phap.value,
            "tong_bua_an":    tong_bua,
            "trung_binh_bua": round(tong_bua / self.so_triet_gia, 2),
            "cho_trung_binh": round(sum(thoi_gian_cho) / self.so_triet_gia, 2),
            "cho_lon_nhat":   round(max(thoi_gian_cho), 2),
            "so_deadlock":    self.so_deadlock,
            "fairness":       round(self._tinh_fairness(so_bua), 4),
            "tung_triet_gia": [tg.lay_thong_ke() for tg in self.triet_gia],
        }

    @staticmethod
    def _tinh_fairness(gia_tri: list[int]) -> float:
        n = len(gia_tri)
        if n == 0 or sum(gia_tri) == 0:
            return 1.0
        tong    = sum(gia_tri)
        tong_bp = sum(v * v for v in gia_tri)
        return (tong * tong) / (n * tong_bp) if tong_bp > 0 else 1.0

    def __repr__(self):
        return (
            f"BanAnToi(so={self.so_triet_gia}, "
            f"giai_phap={self.giai_phap.name}, "
            f"dang_chay={self.dang_chay})"
        )