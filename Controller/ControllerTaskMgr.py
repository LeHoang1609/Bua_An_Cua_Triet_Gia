import logging
import threading
from Model.he_thong.QuetTienTrinh import lay_danh_sach, ket_thuc, lay_thong_tin_he_thong, ThongTinTienTrinh

logger = logging.getLogger(__name__)

REFRESH_MS   = 1500   
MAX_PROCESS  = 50    


class ControllerTaskMgr:
    """
    Controller cho module Task Manager.
    """

    def __init__(self, view):
        self.view      = view
        self._refresh_job = None
        self._dung_gia_lap()
        self._override_kill()
        self.bat_dau_refresh()

    # ── Khởi động ────────────────────────────────────────────────────────

    def _dung_gia_lap(self):
        """
        Dừng vòng lặp giả lập animate_stats() của View.
        Đặt cờ running = False để after() tiếp theo không tự gọi lại.
        """
        try:
            self.view.running = False
            logger.info("Đã dừng vòng lặp giả lập của ViewTaskManger")
        except Exception as e:
            logger.warning(f"Không dừng được giả lập: {e}")

    def _override_kill(self):
        """
        Gắn đè kill_selected của View bằng phiên bản dùng psutil thật.
        """
        def kill_that():
            sel = self.view.tree.selection()
            if not sel:
                return

            pid_str = self.view.tree.item(sel[0])["values"][0]
            try:
                pid = int(pid_str)
            except (ValueError, TypeError):
                return

            ket_qua = ket_thuc(pid)

            if ket_qua.thanh_cong:
                self.view.log_activity(ket_qua.thong_bao, "error")
                # Xóa khỏi bảng ngay lập tức
                if self.view.tree.exists(str(pid)):
                    self.view.tree.delete(str(pid))
            else:
                self.view.log_activity(f"⚠ {ket_qua.thong_bao}", "warn")

        self.view.kill_selected = kill_that
        try:
            self.view.btn_kill.config(command=kill_that)
        except Exception:
            pass

    def bat_dau_refresh(self):
        """Bắt đầu vòng lặp cập nhật dữ liệu thật."""
        self._cap_nhat()

    def dung_refresh(self):
        """Dừng vòng lặp refresh."""
        if self._refresh_job:
            self.view.after_cancel(self._refresh_job)
            self._refresh_job = None

    # ── Cập nhật định kỳ (Background Worker) ─────────────────────────────

    def _cap_nhat(self):
        """Lấy dữ liệu thật từ Model (Background) và đẩy lên View (Main Thread)."""
        
        def worker_fetch_data():
            try:
                # Chạy ngầm psutil để quét hệ thống
                thong_tin = lay_thong_tin_he_thong()
                ds = lay_danh_sach(
                    sap_xep_theo="cpu",
                    giam_dan=True,
                    gioi_han=MAX_PROCESS,
                )
                
                # Gọi luồng chính (Main Thread) để vẽ dữ liệu
                self.view.after(0, lambda: self._apply_data_to_ui(thong_tin, ds))
            except Exception as e:
                logger.error(f"Lỗi refresh TaskMgr: {e}")

        # Tạo và khởi chạy Thread để nó không khóa giao diện
        threading.Thread(target=worker_fetch_data, daemon=True).start()

        # Lên lịch lần kế tiếp
        self._refresh_job = self.view.after(REFRESH_MS, self._cap_nhat)

    def _apply_data_to_ui(self, thong_tin, ds):
        """Luồng chính thực thi việc cập nhật giao diện"""
        try:
            # 1. Cập nhật Dashboard
            cpu_pct = thong_tin["cpu_tong"]
            ram_pct = thong_tin["ram_phan_tram"]
            ram_mb  = thong_tin["ram_dung_mb"]
            ram_total = thong_tin["ram_tong_mb"]

            self.view.lbl_cpu.config(text=f"CPU: {cpu_pct}%")
            self.view.lbl_ram.config(
                text=f"RAM: {ram_mb:.0f} MB / {ram_total:.0f} MB"
            )

            self.view.bar_cpu["value"] = min(100, cpu_pct)
            self.view.bar_ram["value"] = min(100, ram_pct)

            cpu_style = (
                "Danger" if cpu_pct > 80
                else "Warn" if cpu_pct > 50
                else "Safe"
            )
            ram_style = (
                "Danger" if ram_pct > 80
                else "Warn" if ram_pct > 60
                else "Safe"
            )
            self.view.bar_cpu.config(style=f"{cpu_style}.Horizontal.TProgressbar")
            self.view.bar_ram.config(style=f"{ram_style}.Horizontal.TProgressbar")

            # 2. Cập nhật Bảng (Treeview)
            pid_moi = {p.pid for p in ds}

            for iid in list(self.view.tree.get_children()):
                try:
                    pid = int(self.view.tree.item(iid)["values"][0])
                    if pid not in pid_moi:
                        self.view.tree.delete(iid)
                except Exception:
                    continue

            for p in ds:
                iid = str(p.pid)
                values = (
                    p.pid,
                    p.ten,
                    f"{p.cpu:.1f}%",
                    f"{p.ram_mb:.1f} MB",
                    p.trang_thai,
                )
                bg_tag = (
                    "danger_cpu" if p.cpu > 70
                    else "warn_cpu" if p.cpu > 40
                    else ""
                )
                fg_tag = p.trang_thai.lower()

                if self.view.tree.exists(iid):
                    self.view.tree.item(iid, values=values, tags=(bg_tag, fg_tag))
                else:
                    self.view.tree.insert(
                        "", "end", iid=iid,
                        values=values,
                        tags=(bg_tag, fg_tag),
                    )
        except Exception as e:
            logger.error(f"Lỗi khi update UI TaskMgr: {e}")