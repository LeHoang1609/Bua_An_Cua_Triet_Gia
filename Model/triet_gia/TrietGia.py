"""
TrietGia.py
-----------
Mỗi triết gia chạy trên một Thread riêng, lặp liên tục theo chu kỳ:

    DANG_NGHI → DANG_DOI → (lấy đũa) → DANG_AN → (thả đũa) → DANG_NGHI

Cách lấy / thả đũa thay đổi tùy GiaiPhap được chọn:

    NAIVE      : lấy đũa trái → chờ đũa phải  (có thể deadlock)
    SEMAPHORE  : xin phép quản gia trước        (tối đa N-1 người ngồi)
    MONITOR    : dùng Condition — chỉ ăn khi cả 2 đũa rảnh
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

NGHI_MIN, NGHI_MAX   = 0.2, 0.5   # suy nghĩ rất nhanh → nhiều va chạm
AN_MIN,   AN_MAX     = 0.3, 0.8   # ăn vừa phải
TIMEOUT_DEADLOCK     = 0.3        # timeout rất ngắn → dễ trigger preempt


class TrietGia(threading.Thread):

    def __init__(self, ma_triet_gia: int, ban_an: "BanAnToi", giai_phap: GiaiPhap):
        super().__init__(name=f"TrietGia-{ma_triet_gia}", daemon=True)

        self.ma          = ma_triet_gia
        self.ban_an      = ban_an
        self.giai_phap   = giai_phap
        self.trang_thai  = TrangThai.DANG_NGHI

        self.dua_trai = ma_triet_gia
        self.dua_phai = (ma_triet_gia + 1) % ban_an.so_triet_gia

        self.so_bua_an            = 0
        self.tong_thoi_gian_cho   = 0.0
        self.so_lan_bi_preempt    = 0      # ← MỚI: đếm số lần bị timeout/cướp đũa
        self._thoi_diem_doi       = 0.0

        self._stop_event = threading.Event()

    def run(self):
        logger.info(f"TrietGia {self.ma} bắt đầu [{self.giai_phap.value}]")
        while not self._stop_event.is_set():
            self._suy_nghi()
            if self._stop_event.is_set():
                break
            self._doi_va_an()

    def dung(self):
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
        elif self.giai_phap == GiaiPhap.MONITOR:
            return self._lay_dua_monitor()
        elif self.giai_phap == GiaiPhap.THU_TU_DUA:
            return self._lay_dua_thu_tu()
        raise ValueError(f"Giải pháp không hợp lệ: {self.giai_phap}")

    def _lay_dua_naive(self) -> bool:
        dua_trai = self.ban_an.dua[self.dua_trai]
        dua_phai = self.ban_an.dua[self.dua_phai]

        dua_trai.cam()
        dua_trai.dang_giu = self.ma
        self.ban_an.thong_bao_thay_doi()

        # Sleep nhỏ để tăng xác suất tất cả cùng cầm đũa trái → deadlock
        time.sleep(random.uniform(0.05, 0.15))

        timeout  = TIMEOUT_DEADLOCK / self.ban_an.toc_do
        lay_duoc = dua_phai.cam(timeout=timeout)

        if lay_duoc:
            dua_phai.dang_giu = self.ma
            self.ban_an.thong_bao_thay_doi()
            return True

        # Timeout: bị "cướp" — tăng đếm
        self.so_lan_bi_preempt += 1
        dua_trai.tha()
        self._doi_trang_thai(TrangThai.BI_DEADLOCK)
        self.ban_an.so_deadlock += 1
        self.ban_an.thong_bao_thay_doi()
        logger.warning(f"TrietGia {self.ma} DEADLOCK → thả đũa {self.dua_trai}")

        self._stop_event.wait(timeout=random.uniform(0.1, 0.5) / self.ban_an.toc_do)
        return False

    def _lay_dua_semaphore(self) -> bool:
        dua_trai = self.ban_an.dua[self.dua_trai]
        dua_phai = self.ban_an.dua[self.dua_phai]

        self.ban_an.quan_gia.acquire()

        dua_trai.cam()
        dua_trai.dang_giu = self.ma

        dua_phai.cam()
        dua_phai.dang_giu = self.ma

        self.ban_an.thong_bao_thay_doi()
        return True

    def _lay_dua_monitor(self) -> bool:
        """
        Monitor: dùng Condition Variable.
        Triết gia chỉ được ăn khi CẢ HAI đũa kề đều rảnh.
        Không bao giờ cầm 1 đũa rồi chờ đũa kia → loại trừ deadlock hoàn toàn.
        """
        trai = self.dua_trai
        phai = self.dua_phai

        with self.ban_an.monitor_condition:
            # Chờ đến khi cả 2 đũa rảnh
            while (
                self.ban_an.dua[trai].dang_giu is not None or
                self.ban_an.dua[phai].dang_giu is not None
            ):
                if self._stop_event.is_set():
                    return False
                # Mỗi lần bị chặn lại tính là 1 lần "bị cướp"
                self.so_lan_bi_preempt += 1
                self.ban_an.monitor_condition.wait(timeout=1.0)

            # Lấy cả 2 đũa trong critical section
            self.ban_an.dua[trai].dang_giu = self.ma
            self.ban_an.dua[phai].dang_giu = self.ma

        self.ban_an.thong_bao_thay_doi()
        return True

    def _lay_dua_thu_tu(self) -> bool:
        nho_hon = min(self.dua_trai, self.dua_phai)
        lon_hon = max(self.dua_trai, self.dua_phai)

        dua_nho = self.ban_an.dua[nho_hon]
        dua_lon = self.ban_an.dua[lon_hon]

        dua_nho.cam()
        dua_nho.dang_giu = self.ma
        self.ban_an.thong_bao_thay_doi()

        dua_lon.cam()
        dua_lon.dang_giu = self.ma
        self.ban_an.thong_bao_thay_doi()

        return True

    def _tha_dua(self):
        dua_trai = self.ban_an.dua[self.dua_trai]
        dua_phai = self.ban_an.dua[self.dua_phai]

        if self.giai_phap == GiaiPhap.MONITOR:
            with self.ban_an.monitor_condition:
                dua_trai.dang_giu = None
                dua_phai.dang_giu = None
                self.ban_an.monitor_condition.notify_all()
        else:
            try:
                dua_trai.tha()
            except RuntimeError:
                pass
            try:
                dua_phai.tha()
            except RuntimeError:
                pass
            if self.giai_phap == GiaiPhap.SEMAPHORE:
                self.ban_an.quan_gia.release()

        self.ban_an.thong_bao_thay_doi()

    def _doi_trang_thai(self, trang_thai: TrangThai):
        self.trang_thai = trang_thai
        self.ban_an.thong_bao_thay_doi()

    def lay_thong_ke(self) -> dict:
        return {
            "ma":                   self.ma,
            "trang_thai":           self.trang_thai.value,
            "so_bua_an":            self.so_bua_an,
            "tong_thoi_gian_cho":   round(self.tong_thoi_gian_cho, 2),
            "so_lan_bi_preempt":    self.so_lan_bi_preempt,   # ← MỚI
            "dua_trai":             self.dua_trai,
            "dua_phai":             self.dua_phai,
        }

    def lay_thoi_gian_cho_hien_tai(self) -> float:
        """Thời gian chờ thực tế tính từ lúc bắt đầu đợi đũa."""
        if self.trang_thai == TrangThai.DANG_DOI and self._thoi_diem_doi > 0:
            return round(time.monotonic() - self._thoi_diem_doi, 1)
        return 0.0

    def __repr__(self):
        return (
            f"TrietGia(ma={self.ma}, "
            f"trang_thai={self.trang_thai.name}, "
            f"giai_phap={self.giai_phap.name})"
        )