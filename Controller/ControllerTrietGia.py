

import threading
import time
import logging

from Model.triet_gia.BanAnToi import BanAnToi
from Model.triet_gia.TrietGia_State import GiaiPhap, TrangThai

logger = logging.getLogger(__name__)

# ── Ánh xạ tên Combobox → GiaiPhap enum ─────────────────────────────────
GIAI_PHAP_MAP = {
    "Không tránh deadlock": GiaiPhap.NAIVE,
    "Semaphore":            GiaiPhap.SEMAPHORE,
    "Monitor":              GiaiPhap.SEMAPHORE,    # Monitor ~ Semaphore trong model
    "Bất đối xứng":         GiaiPhap.THU_TU_DUA,
}

# ── Ánh xạ TrangThai → tên state mà View hiểu ───────────────────────────
TRANG_THAI_MAP = {
    TrangThai.DANG_NGHI:   "thinking",
    TrangThai.DANG_DOI:    "hungry",
    TrangThai.DANG_AN:     "eating",
    TrangThai.BI_DEADLOCK: "blocked",
}

# Ngưỡng thời gian chờ để chuyển sang "starving" (giây)
STARVING_NGUONG = 6.0


class ControllerTrietGia:
    """
    Controller cho module Triết gia.

    Tham số:
        view : instance của ViewTrietGia
    """

    def __init__(self, view):
        self.view      = view
        self.ban_an: None
        self._push_job = None     # after() job ID đang chạy

    # ── Lệnh từ View ─────────────────────────────────────────────────────

    def start_simulation(self, ten_giai_phap: str):
        giai_phap = self._map_giai_phap(ten_giai_phap)

        if self.ban_an and self.ban_an.dang_chay:
            if self.ban_an.giai_phap == giai_phap:
                return
            self._stop_model()

        self.ban_an = BanAnToi(
            so_triet_gia=5,
            giai_phap=giai_phap,
            toc_do=1.5,
    )
        self.ban_an.dang_ky_thay_doi(self._on_model_change)
        self.ban_an.bat_dau()

        logger.info(f"Bắt đầu: {ten_giai_phap}")
    # Gọi _schedule_push sau 100ms để đảm bảo mainloop đang chạy
        self.view.after(100, self._schedule_push)

    def step_simulation(self, ten_giai_phap: str):
        """
        View gọi khi nhấn ⏭ Bước.
        Chạy model 1 giây rồi tạm dừng, đẩy 1 snapshot về View.
        """
        giai_phap = self._map_giai_phap(ten_giai_phap)

        # Khởi tạo nếu chưa có hoặc sai giải pháp
        if not self.ban_an or self.ban_an.giai_phap != giai_phap:
            if self.ban_an:
                self._stop_model()
            self.ban_an = BanAnToi(
                so_triet_gia=5,
                giai_phap=giai_phap,
                toc_do=3.0,   # chạy nhanh hơn để thấy thay đổi ngay
            )
            self.ban_an.dang_ky_thay_doi(self._on_model_change)
            self.ban_an.bat_dau()

        # Cho model chạy 0.8s rồi đẩy snapshot
        def _run_step():
            time.sleep(0.8)
            self._push_snapshot()

        threading.Thread(target=_run_step, daemon=True).start()

    def stop_simulation(self):
        """View gọi khi nhấn ⏸ Dừng."""
        self._dung_push_ui()
        if self.ban_an:
            self.ban_an.tam_dung()

    def reset_simulation(self):
        """View gọi khi nhấn 🔄 Reset."""
        self._dung_push_ui()
        self._stop_model()

    # ── Cập nhật UI định kỳ ──────────────────────────────────────────────

    def _bat_dau_push_ui(self):
        self._dung_push_ui()
        self.view.after(100, self._schedule_push)

    def _schedule_push(self):
        """Lên lịch push tiếp theo (chạy trên main thread qua after())."""
        if self.ban_an and self.ban_an.dang_chay:
            self._push_snapshot()
            self._push_job = self.view.after(500, self._schedule_push)

    def _dung_push_ui(self):
        if self._push_job:
            self.view.after_cancel(self._push_job)
            self._push_job = None

    # ── Callback từ Model ─────────────────────────────────────────────────

    def _on_model_change(self):
    # Không làm gì — để _schedule_push tự cập nhật định kỳ
        pass

    # ── Đẩy snapshot về View ─────────────────────────────────────────────

    def _push_snapshot(self):
        """Lấy snapshot từ Model và gọi View.update_snapshot()."""
        if not self.ban_an:
            return

        snap = self.ban_an.lay_snapshot()
        tg_list = snap["triet_gia"]

        # Chuyển đổi trạng thái
        states        = []
        wait_times    = []
        stolen_counts = []   # Model chưa có "bị cướp", dùng số deadlock escape

        for tg in tg_list:
            state_raw = tg["trang_thai"]

            # Tìm ngược TrangThai enum từ value string
            trang_thai_enum = next(
                (t for t in TrangThai if t.value == state_raw),
                TrangThai.DANG_NGHI
            )

            # Kiểm tra starving: đang đợi quá lâu
            state_ui = TRANG_THAI_MAP.get(trang_thai_enum, "thinking")
            if state_ui == "hungry":
                wait = tg["tong_thoi_gian_cho"]
                if wait > STARVING_NGUONG:
                    state_ui = "starving"

            states.append(state_ui)
            wait_times.append(round(tg["tong_thoi_gian_cho"], 1))
            stolen_counts.append(0)   # mở rộng sau

        try:
            self.view.update_snapshot(states, wait_times, stolen_counts)
        except Exception as e:
            logger.error(f"Lỗi update_snapshot: {e}")

    # ── Tiện ích ─────────────────────────────────────────────────────────

    def _map_giai_phap(self, ten: str) -> GiaiPhap:
        gp = GIAI_PHAP_MAP.get(ten)
        if not gp:
            logger.warning(f"Giải pháp '{ten}' không tìm thấy, dùng NAIVE")
            return GiaiPhap.NAIVE
        return gp

    def _stop_model(self):
        if self.ban_an:
            self.ban_an.dung()
            self.ban_an = None