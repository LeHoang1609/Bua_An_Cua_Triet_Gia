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
    "Monitor":              GiaiPhap.MONITOR,      # ← Sửa: Monitor thực sự
    "Bất đối xứng":         GiaiPhap.THU_TU_DUA,
}

# ── Ánh xạ TrangThai → tên state mà View hiểu ───────────────────────────
TRANG_THAI_MAP = {
    TrangThai.DANG_NGHI:   "thinking",
    TrangThai.DANG_DOI:    "hungry",
    TrangThai.DANG_AN:     "eating",
    TrangThai.BI_DEADLOCK: "blocked",
}

# Ngưỡng thời gian chờ hiện tại để chuyển sang "starving" (giây)
STARVING_NGUONG = 3.0


class ControllerTrietGia:

    def __init__(self, view):
        self.view      = view
        self.ban_an    = None
        self._push_job     = None
        self._push_running = False    # ← chống tạo nhiều push job chồng nhau

    # ── Lệnh từ View ─────────────────────────────────────────────────────

    def start_simulation(self, ten_giai_phap: str):
        giai_phap = self._map_giai_phap(ten_giai_phap)

        if self.ban_an and self.ban_an.dang_chay:
            if self.ban_an.giai_phap == giai_phap:
                return
            self._stop_model()

        # Reset View về trạng thái sạch trước khi chạy mới
        try:
            self.view.update_snapshot(["thinking"] * 5, [0] * 5, [0] * 5, 0)
        except Exception:
            pass

        self.ban_an = BanAnToi(
            so_triet_gia=5,
            giai_phap=giai_phap,
            toc_do=1.0,
        )
        self.ban_an.dang_ky_thay_doi(self._on_model_change)
        self.ban_an.bat_dau()

        logger.info(f"Bắt đầu: {ten_giai_phap}")
        self._bat_dau_push_ui()

    def step_simulation(self, ten_giai_phap: str):
        giai_phap = self._map_giai_phap(ten_giai_phap)

        if not self.ban_an or self.ban_an.giai_phap != giai_phap:
            if self.ban_an:
                self._stop_model()
            try:
                self.view.update_snapshot(["thinking"] * 5, [0] * 5, [0] * 5, 0)
            except Exception:
                pass
            self.ban_an = BanAnToi(
                so_triet_gia=5,
                giai_phap=giai_phap,
                toc_do=3.0,
            )
            self.ban_an.dang_ky_thay_doi(self._on_model_change)
            self.ban_an.bat_dau()

        def _run_step():
            time.sleep(0.8)
            self.view.after(0, self._push_snapshot)

        threading.Thread(target=_run_step, daemon=True).start()

    def stop_simulation(self):
        self._dung_push_ui()
        if self.ban_an:
            self.ban_an.tam_dung()

    def reset_simulation(self):
        self._dung_push_ui()
        self._stop_model()

    # ── Cập nhật UI định kỳ ──────────────────────────────────────────────

    def _bat_dau_push_ui(self):
        self._dung_push_ui()
        self._push_running = True
        self.view.after(100, self._schedule_push)

    def _schedule_push(self):
        if self.ban_an and self.ban_an.dang_chay and self._push_running:
            self._push_snapshot()
            self._push_job = self.view.after(500, self._schedule_push)

    def _dung_push_ui(self):
        self._push_running = False
        if self._push_job:
            self.view.after_cancel(self._push_job)
            self._push_job = None

    # ── Callback từ Model ─────────────────────────────────────────────────

    def _on_model_change(self):
        pass

    # ── Đẩy snapshot về View ─────────────────────────────────────────────

    def _push_snapshot(self):
        if not self.ban_an:
            return

        snap    = self.ban_an.lay_snapshot()
        tg_list = snap["triet_gia"]
        cho_hien_tai = snap.get("triet_gia_cho_hien_tai", [0] * 5)

        states        = []
        wait_times    = []
        stolen_counts = []

        for i, tg in enumerate(tg_list):
            state_raw = tg["trang_thai"]

            trang_thai_enum = next(
                (t for t in TrangThai if t.value == state_raw),
                TrangThai.DANG_NGHI
            )

            state_ui = TRANG_THAI_MAP.get(trang_thai_enum, "thinking")

            # Starving: dùng thời gian chờ HIỆN TẠI (tính từ lúc bắt đầu đợi đũa)
            if state_ui == "hungry":
                current_wait = cho_hien_tai[i] if i < len(cho_hien_tai) else 0
                if current_wait > STARVING_NGUONG:
                    state_ui = "starving"

            states.append(state_ui)
            # Hiển thị TG Chờ tích lũy (tổng các lần đã chờ thành công)
            wait_times.append(tg["tong_thoi_gian_cho"])
            stolen_counts.append(tg["so_lan_bi_preempt"])   # ← Sửa: dùng giá trị thực

        so_deadlock = snap.get("so_deadlock", 0)

        try:
            self.view.update_snapshot(states, wait_times, stolen_counts, so_deadlock)
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