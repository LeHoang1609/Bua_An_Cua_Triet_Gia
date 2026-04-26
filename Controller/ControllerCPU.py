

import logging
from Model.lap_lich.Tien_Trinh import TienTrinh, KetQuaTienTrinh, KhoangGantt
from Model.lap_lich.Giai_Thuat import KetQuaLapLich, fcfs, sjf, priority, round_robin

logger = logging.getLogger(__name__)

# ── Ánh xạ tên Combobox → hàm thuật toán ────────────────────────────────
ALGO_MAP = {
    "FCFS (First Come First Serve)": "fcfs",
    "SJF (Non Preemptive)":          "sjf",
    "SRTF (Preemptive)":             "sjf",      
    "Priority":                      "priority",
    "Round Robin":                   "round_robin",
}


class ControllerCPU:


    def __init__(self, view):
        self.view = view

    # ── Lệnh từ View ─────────────────────────────────────────────────────

    def run_cpu_scheduling(self, processes: list[dict], algo: str, quantum: float):
        """
        View gọi khi nhấn 🚀 CHẠY MÔ PHỎNG.

        Tham số:
            processes : list[{"pid", "arrival", "burst", "priority"}]
            algo      : tên thuật toán từ Combobox
            quantum   : time quantum (chỉ dùng khi Round Robin)
        """
        # ── 1. Validate & chuyển đổi sang TienTrinh ──────────────────────
        tien_trinh_list = self._chuyen_doi_tien_trinh(processes)
        if not tien_trinh_list:
            logger.warning("Danh sách tiến trình rỗng hoặc không hợp lệ")
            return

        # ── 2. Chọn thuật toán ────────────────────────────────────────────
        ket_qua = self._chay_thuat_toan(algo, tien_trinh_list, quantum)
        if not ket_qua:
            return

        # ── 3. Chuyển đổi kết quả sang định dạng View hiểu ───────────────
        gantt_data = self._chuyen_gantt(ket_qua)
        awt  = ket_qua.avg_waiting_time
        atat = ket_qua.avg_turnaround_time

        logger.info(
            f"[{ket_qua.thuat_toan}] "
            f"AWT={awt}ms ATAT={atat}ms "
            f"({len(tien_trinh_list)} tiến trình)"
        )

        # ── 4. Đẩy kết quả về View ────────────────────────────────────────
        try:
            self.view.update_result(gantt_data, awt, atat)
        except Exception as e:
            logger.error(f"Lỗi update_result: {e}")

    # ── Xử lý nội bộ ─────────────────────────────────────────────────────

    def _chuyen_doi_tien_trinh(self, processes: list[dict]) -> list[TienTrinh]:
        """
        Chuyển list dict từ View sang list TienTrinh.
        Bỏ qua các tiến trình có dữ liệu không hợp lệ.
        """
        ket_qua = []
        for p in processes:
            try:
                tt = TienTrinh(
                    ten          = str(p["pid"]),
                    burst_time   = max(1, int(float(p["burst"]))),
                    arrival_time = max(0, int(float(p["arrival"]))),
                    priority     = int(p.get("priority", 0)),
                )
                ket_qua.append(tt)
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Bỏ qua tiến trình không hợp lệ {p}: {e}")
        return ket_qua

    def _chay_thuat_toan(
        self,
        algo: str,
        ds: list[TienTrinh],
        quantum: float,
    ) -> KetQuaLapLich | None:
        """Gọi hàm thuật toán tương ứng từ Model."""
        ten_algo = ALGO_MAP.get(algo, "fcfs")

        try:
            if ten_algo == "fcfs":
                return fcfs(ds)
            elif ten_algo == "sjf":
                return sjf(ds)
            elif ten_algo == "priority":
                return priority(ds)
            elif ten_algo == "round_robin":
                q = max(1, int(quantum)) if quantum else 2
                return round_robin(ds, quantum=q)
            else:
                logger.warning(f"Không nhận ra thuật toán '{algo}', dùng FCFS")
                return fcfs(ds)
        except Exception as e:
            logger.error(f"Lỗi khi chạy thuật toán {algo}: {e}")
            return None

    def _chuyen_gantt(self, ket_qua: KetQuaLapLich) -> list[dict]:
        """
        Chuyển list[KhoangGantt] → list[{"pid", "start", "end"}]
        đúng định dạng View.draw_gantt_chart_animated() cần.
        """
        return [
            {
                "pid":   g.ten,        # "P1", "P2", ... hoặc "idle"
                "start": g.bat_dau,
                "end":   g.ket_thuc,
            }
            for g in ket_qua.gantt
        ]