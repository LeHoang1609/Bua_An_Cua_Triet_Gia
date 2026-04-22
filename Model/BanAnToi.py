import threading
import time
import logging
from typing import Callable

from .ChiecDua import Fork
from .TrietGia import Philosopher
from .TrietGia_State import State, Solution, PhilosopherStats

logger = logging.getLogger(__name__)


class BanAnTrieuGia:
    """
    Quản lý toàn bộ trạng thái bài toán Dining Philosophers.
    """

    MIN_TRIET_GIA = 3
    MAX_TRIET_GIA = 8

    def __init__(
        self,
        so_triet_gia: int = 5,
        giai_phap: Solution = Solution.NAIVE,
        toc_do: float = 1.0,
    ):
        if not (self.MIN_TRIET_GIA <= so_triet_gia <= self.MAX_TRIET_GIA):
            raise ValueError(
                f"Số triết gia phải từ {self.MIN_TRIET_GIA} đến {self.MAX_TRIET_GIA}"
            )

        self.so_triet_gia = so_triet_gia
        self.giai_phap = giai_phap
        self.toc_do = toc_do
        self.danh_sach_dua: list[Fork] = [Fork(i) for i in range(so_triet_gia)]
        self.bo_dieu_phoi = threading.Semaphore(so_triet_gia - 1)
        self.dieu_kien_dua: list[threading.Condition] = [
            threading.Condition(threading.Lock()) for _ in range(so_triet_gia)
        ]
        self.yeu_cau_dua: list[set[int]] = [set() for _ in range(so_triet_gia)]
        self.danh_sach_triet_gia: list[Philosopher] = [
            Philosopher(i, self, giai_phap) for i in range(so_triet_gia)
        ]
        self.dang_chay: bool = False
        self.tam_dung: bool = False
        self.so_lan_deadlock: int = 0
        self.so_lan_starvation: int = 0
        self.thoi_diem_bat_dau: float | None = None
        self._ham_thong_bao: Callable | None = None
        self._khoa_thong_bao = threading.Lock()

    def bat_dau(self):
        if self.dang_chay:
            logger.warning("Simulation đang chạy")
            return

        self.dang_chay = True
        self.tam_dung = False
        self.thoi_diem_bat_dau = time.monotonic()

        for tg in self.danh_sach_triet_gia:
            tg.start()

        logger.info(
            f"Start: {self.so_triet_gia} triết gia, giải pháp = {self.giai_phap.value}"
        )

    def dung(self):
        if not self.dang_chay:
            return

        self.dang_chay = False
        self.tam_dung = False

        for tg in self.danh_sach_triet_gia:
            tg.stop()
        for dk in self.dieu_kien_dua:
            with dk:
                dk.notify_all()

        for tg in self.danh_sach_triet_gia:
            tg.join(timeout=3.0)

        logger.info("Đã dừng")

    def tam_dung_mo_phong(self):
        self.tam_dung = True
        logger.info("Tạm dừng")

    def tiep_tuc(self):
        self.tam_dung = False
        logger.info("Tiếp tục")
    def dat_giai_phap(self, giai_phap: Solution):
        self.giai_phap = giai_phap

    def dat_toc_do(self, toc_do: float):
        if toc_do <= 0:
            raise ValueError("Tốc độ phải > 0")
        self.toc_do = toc_do
        logger.info(f"Tốc độ: {toc_do}x")

    def reset(self, so_triet_gia: int = None, giai_phap: Solution = None):
        self.dung()

        n = so_triet_gia or self.so_triet_gia
        gp = giai_phap or self.giai_phap
        self.__init__(n, gp, self.toc_do)

        logger.info(f"Reset: {n} triết gia")

    def dang_ky_callback(self, ham: Callable):
        self._ham_thong_bao = ham

    def thong_bao_thay_doi(self):
        if self._ham_thong_bao:
            try:
                self._ham_thong_bao()
            except Exception as e:
                logger.error(f"Lỗi callback: {e}")

    def lay_trang_thai(self) -> dict:
        thoi_gian = (
            round(time.monotonic() - self.thoi_diem_bat_dau, 1)
            if self.thoi_diem_bat_dau else 0.0
        )

        return {
            "so_triet_gia": self.so_triet_gia,
            "giai_phap": self.giai_phap.value,
            "dang_chay": self.dang_chay,
            "tam_dung": self.tam_dung,
            "toc_do": self.toc_do,
            "thoi_gian": thoi_gian,
            "deadlock": self.so_lan_deadlock,
            "starvation": self.so_lan_starvation,
            "triet_gia": [p.to_dict() for p in self.danh_sach_triet_gia],
            "dua": [
                {
                    "id": f.fork_id,
                    "dang_su_dung": f.is_held,
                    "boi_ai": f.held_by,
                    "dirty": f.dirty,
                }
                for f in self.danh_sach_dua
            ],
        }

    def tong_ket(self) -> dict:
        so_lan_an = [p.stats.total_meals for p in self.danh_sach_triet_gia]
        thoi_gian_cho = [p.stats.total_wait_time for p in self.danh_sach_triet_gia]

        tong = sum(so_lan_an)
        fairness = self._jain_fairness(so_lan_an)

        return {
            "tong_so_lan_an": tong,
            "trung_binh": round(tong / self.so_triet_gia, 2),
            "cho_max": round(max(thoi_gian_cho), 2),
            "cho_tb": round(sum(thoi_gian_cho) / self.so_triet_gia, 2),
            "fairness": round(fairness, 4),
        }



    @staticmethod
    def _jain_fairness(values: list[int]) -> float:
        n = len(values)
        if n == 0 or sum(values) == 0:
            return 1.0

        s1 = sum(values)
        s2 = sum(v * v for v in values)

        return (s1 * s1) / (n * s2) if s2 > 0 else 1.0

    def __repr__(self):
        return (
            f"BanAnTrieuGia(n={self.so_triet_gia}, "
            f"giai_phap={self.giai_phap.name}, "
            f"dang_chay={self.dang_chay})"
        )