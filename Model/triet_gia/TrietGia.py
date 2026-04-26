"""
TrietGia.py
-----------
Mỗi triết gia chạy trên một Thread riêng, lặp liên tục theo chu kỳ:

    DANG_NGHI → DANG_DOI → (lấy đũa) → DANG_AN → (thả đũa) → DANG_NGHI

Cách lấy / thả đũa thay đổi tùy GiaiPhap được chọn:

    NAIVE      : lấy đũa trái → chờ đũa phải  (có thể deadlock)
    SEMAPHORE  : xin phép quản gia trước        (tối đa N-1 người ngồi)
    THU_TU_DUA : luôn lấy đũa số nhỏ hơn trước (không bao giờ deadlock)
"""

import threading
import time
import random
import logging
from typing import TYPE_CHECKING

from .TrietGia_State import TrangThai, GiaiPhap

if TYPE_CHECKING:
    from .BanAnToi import BanAnToi

logger = logging.getLogger(__name__)

NGHI_MIN, NGHI_MAX   = 1.0, 3.0    
AN_MIN,   AN_MAX     = 1.0, 2.5    
TIMEOUT_DEADLOCK     = 5.0         


class TrietGia(threading.Thread):

    def __init__(self, ma_triet_gia: int, ban_an: "BanAnToi", giai_phap: GiaiPhap):
        super().__init__(name=f"TrietGia-{ma_triet_gia}", daemon=True)

        self.ma          = ma_triet_gia
        self.ban_an      = ban_an
        self.giai_phap   = giai_phap
        self.trang_thai  = TrangThai.DANG_NGHI

        self.dua_trai = ma_triet_gia
        self.dua_phai = (ma_triet_gia + 1) % ban_an.so_triet_gia

        self.so_bua_an       = 0
        self.tong_thoi_gian_cho = 0.0    
        self._thoi_diem_doi  = 0.0

        self._stop_event = threading.Event()

    def run(self):
        logger.info(f"TrietGia {self.ma} bắt đầu [{self.giai_phap.value}]")
        while not self._stop_event.is_set():
            self._suy_nghi()
            if self._stop_event.is_set():
                break
            self._doi_va_an()

    def dung(self):
        """Yêu cầu dừng thread."""
        self._stop_event.set()


    def _suy_nghi(self):
        self._doi_trang_thai(TrangThai.DANG_NGHI)
        thoi_gian = random.uniform(NGHI_MIN, NGHI_MAX) / self.ban_an.toc_do
        self._stop_event.wait(timeout=thoi_gian)


    def _doi_va_an(self):
        self._doi_trang_thai(TrangThai.DANG_DOI)
        self._thoi_diem_doi = time.monotonic()

        lay_duoc = self._lay_dua()

        if not lay_duoc or self._stop_event.is_set():
            return

        self.tong_thoi_gian_cho += time.monotonic() - self._thoi_diem_doi

        self._doi_trang_thai(TrangThai.DANG_AN)
        self.so_bua_an += 1
        thoi_gian = random.uniform(AN_MIN, AN_MAX) / self.ban_an.toc_do
        self._stop_event.wait(timeout=thoi_gian)

        self._tha_dua()


    def _lay_dua(self) -> bool:
        if self.giai_phap == GiaiPhap.NAIVE:
            return self._lay_dua_naive()
        elif self.giai_phap == GiaiPhap.SEMAPHORE:
            return self._lay_dua_semaphore()
        elif self.giai_phap == GiaiPhap.THU_TU_DUA:
            return self._lay_dua_thu_tu()
        raise ValueError(f"Giải pháp không hợp lệ: {self.giai_phap}")

    def _lay_dua_naive(self) -> bool:
        dua_trai = self.ban_an.dua[self.dua_trai]
        dua_phai = self.ban_an.dua[self.dua_phai]

        dua_trai.cam()
        dua_trai.dang_giu = self.ma
        self.ban_an.thong_bao_thay_doi()
        logger.debug(f"TrietGia {self.ma} cầm đũa trái {self.dua_trai}")

        timeout = TIMEOUT_DEADLOCK / self.ban_an.toc_do
        lay_duoc = dua_phai.cam(timeout=timeout)

        if lay_duoc:
            dua_phai.dang_giu = self.ma
            self.ban_an.thong_bao_thay_doi()
            logger.debug(f"TrietGia {self.ma} cầm đũa phải {self.dua_phai}")
            return True

        dua_trai.tha()
        self._doi_trang_thai(TrangThai.BI_DEADLOCK)
        self.ban_an.so_deadlock += 1
        self.ban_an.thong_bao_thay_doi()
        logger.warning(f"TrietGia {self.ma} DEADLOCK → thả đũa {self.dua_trai}")

        self._stop_event.wait(timeout=random.uniform(0.5, 1.5) / self.ban_an.toc_do)
        return False

    def _lay_dua_semaphore(self) -> bool:
        dua_trai = self.ban_an.dua[self.dua_trai]
        dua_phai = self.ban_an.dua[self.dua_phai]

        self.ban_an.quan_gia.acquire()
        logger.debug(f"TrietGia {self.ma} được quản gia cho phép ngồi")

        dua_trai.cam()
        dua_trai.dang_giu = self.ma

        dua_phai.cam()
        dua_phai.dang_giu = self.ma

        self.ban_an.thong_bao_thay_doi()
        logger.debug(f"TrietGia {self.ma} cầm đũa {self.dua_trai} & {self.dua_phai} (semaphore)")
        return True

    def _lay_dua_thu_tu(self) -> bool:
        nho_hon = min(self.dua_trai, self.dua_phai)
        lon_hon = max(self.dua_trai, self.dua_phai)

        dua_nho = self.ban_an.dua[nho_hon]
        dua_lon = self.ban_an.dua[lon_hon]

        dua_nho.cam()
        dua_nho.dang_giu = self.ma
        self.ban_an.thong_bao_thay_doi()
        logger.debug(f"TrietGia {self.ma} cầm đũa {nho_hon} (nhỏ hơn)")

        dua_lon.cam()
        dua_lon.dang_giu = self.ma
        self.ban_an.thong_bao_thay_doi()
        logger.debug(f"TrietGia {self.ma} cầm đũa {lon_hon} (lớn hơn)")

        return True

    def _tha_dua(self):
        dua_trai = self.ban_an.dua[self.dua_trai]
        dua_phai = self.ban_an.dua[self.dua_phai]

        dua_trai.tha()
        dua_phai.tha()
        if self.giai_phap == GiaiPhap.SEMAPHORE:
            self.ban_an.quan_gia.release()

        self.ban_an.thong_bao_thay_doi()
        logger.debug(f"TrietGia {self.ma} thả đũa {self.dua_trai} & {self.dua_phai}")

    def _doi_trang_thai(self, trang_thai: TrangThai):
        self.trang_thai = trang_thai
        self.ban_an.thong_bao_thay_doi()

    def lay_thong_ke(self) -> dict:
        return {
            "ma":                self.ma,
            "trang_thai":        self.trang_thai.value,
            "so_bua_an":         self.so_bua_an,
            "tong_thoi_gian_cho": round(self.tong_thoi_gian_cho, 2),
            "dua_trai":          self.dua_trai,
            "dua_phai":          self.dua_phai,
        }

    def __repr__(self):
        return (
            f"TrietGia(ma={self.ma}, "
            f"trang_thai={self.trang_thai.name}, "
            f"giai_phap={self.giai_phap.name})"
        )