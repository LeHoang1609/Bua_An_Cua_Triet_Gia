import logging
import threading
import random
import tkinter as tk
from tkinter import messagebox
from Model.he_thong.QuetTienTrinh import lay_danh_sach, ket_thuc, lay_thong_tin_he_thong, ThongTinTienTrinh

logger = logging.getLogger(__name__)

REFRESH_MS   = 3000   
MAX_PROCESS  = 50    

class ControllerTaskMgr:
    def __init__(self, view):
        self.view      = view
        self._refresh_job = None
        self.tien_trinh_gia = []  
        self.thong_tin_hien_tai = None  # Biến mới lưu trữ tạm để update UI tức thì
        
        self.da_canh_bao_oom = False
        self.da_canh_bao_vang = False
        
        self._dung_gia_lap()
        self._bind_buttons()
        self.bat_dau_refresh()

    def _dung_gia_lap(self):
        try:
            self.view.running = False
        except Exception:
            pass

    def _bind_buttons(self):
        def _find_btns(widget):
            res = []
            for child in widget.winfo_children():
                if isinstance(child, tk.Button):
                    res.append(child)
                res.extend(_find_btns(child))
            return res

        try:
            btns = _find_btns(self.view)
            for b in btns:
                txt = b.cget("text")
                if "End Task" in txt:
                    b.config(command=self.kill_selected)
                elif "New Task" in txt:
                    b.config(command=self.tao_tien_trinh_gia)
        except Exception as e:
            logger.warning(f"Không bind được nút: {e}")

    # ── XỬ LÝ NÚT BẤM (Cập nhật giao diện tức thì) ──────────────────────────────

    def tao_tien_trinh_gia(self):
        pid = random.randint(90000, 99999) 
        is_leak = random.random() < 0.4
        name = "[Ảo] LeakApp.exe" if is_leak else random.choice(["[Ảo] Chrome.exe", "[Ảo] Spotify.exe", "[Ảo] Game.exe"])
        
        fake_p = ThongTinTienTrinh(
            pid=pid, ten=name, cpu=random.uniform(2.0, 8.0), 
            ram_mb=random.uniform(200.0, 500.0), ram_phan_tram=2.0, 
            trang_thai="Running", nguoi_dung="Mô Phỏng"
        )
        fake_p.is_leak = is_leak 
        
        self.tien_trinh_gia.append(fake_p)
        self.view.log_activity(f"➕ Tạo tiến trình ảo: {name} (PID: {pid})", "success")
        
        # 1. THÊM NGAY LÊN ĐẦU BẢNG MÀ KHÔNG CHỜ QUÉT PHẦN CỨNG
        iid = str(fake_p.pid)
        values = (fake_p.pid, fake_p.ten, f"{fake_p.cpu:.1f}%", f"{fake_p.ram_mb:.0f} MB", fake_p.trang_thai)
        if not self.view.tree.exists(iid):
            self.view.tree.insert("", "0", iid=iid, values=values, tags=("warn_cpu", fake_p.trang_thai.lower()))

        # 2. CỘNG DỒN RAM VÀ VẼ LẠI THANH TỨC THÌ
        if self.thong_tin_hien_tai:
            self.thong_tin_hien_tai["ram_dung_mb"] += fake_p.ram_mb
            if self.thong_tin_hien_tai["ram_tong_mb"] > 0:
                self.thong_tin_hien_tai["ram_phan_tram"] = min(100.0, (self.thong_tin_hien_tai["ram_dung_mb"] / self.thong_tin_hien_tai["ram_tong_mb"]) * 100)
            self._update_dashboard_ui(self.thong_tin_hien_tai)

    def kill_selected(self):
        sel = self.view.tree.selection()
        if not sel: return
        
        pid_str = self.view.tree.item(sel[0])["values"][0]
        try: 
            pid = int(pid_str)
        except ValueError: 
            return

        for fp in self.tien_trinh_gia:
            if fp.pid == pid:
                self.tien_trinh_gia.remove(fp)
                self.view.log_activity(f"❌ Đã đóng ứng dụng ảo: {fp.ten}", "success")
                
                # 1. XÓA NGAY KHỎI BẢNG
                if self.view.tree.exists(str(pid)):
                    self.view.tree.delete(str(pid))
                
                # 2. TRỪ RAM VÀ VẼ LẠI THANH TỨC THÌ
                if self.thong_tin_hien_tai:
                    self.thong_tin_hien_tai["ram_dung_mb"] = max(0, self.thong_tin_hien_tai["ram_dung_mb"] - fp.ram_mb)
                    if self.thong_tin_hien_tai["ram_tong_mb"] > 0:
                        self.thong_tin_hien_tai["ram_phan_tram"] = min(100.0, (self.thong_tin_hien_tai["ram_dung_mb"] / self.thong_tin_hien_tai["ram_tong_mb"]) * 100)
                    self._update_dashboard_ui(self.thong_tin_hien_tai)
                return

        # Nếu là app hệ thống thật
        ket_qua = ket_thuc(pid)
        if ket_qua.thanh_cong:
            self.view.log_activity(ket_qua.thong_bao, "success")
            if self.view.tree.exists(str(pid)):
                self.view.tree.delete(str(pid))
        else:
            self.view.log_activity(f"⚠ Từ chối: Cần quyền Admin để đóng {pid_str}", "warn")

    # ── VÒNG LẶP CẬP NHẬT ────────────────────────────────────────────────

    def bat_dau_refresh(self):
        self._cap_nhat_loop()

    def dung_refresh(self):
        if self._refresh_job:
            self.view.after_cancel(self._refresh_job)
            self._refresh_job = None

    def _cap_nhat_loop(self):
        self._fetch_and_draw()
        self._refresh_job = self.view.after(REFRESH_MS, self._cap_nhat_loop)

    def _fetch_and_draw(self):
        fake_cpu = 0
        fake_ram = 0
        for fp in self.tien_trinh_gia:
            fp.cpu = max(0.1, round(fp.cpu + random.uniform(-2, 2), 1))
            if getattr(fp, 'is_leak', False):
                fp.ram_mb += random.uniform(80, 150) 
            else:
                fp.ram_mb = max(10, round(fp.ram_mb + random.uniform(-5, 5), 1))
            fake_cpu += fp.cpu
            fake_ram += fp.ram_mb

        def worker_fetch_data():
            try:
                thong_tin = lay_thong_tin_he_thong()
                ds = lay_danh_sach(sap_xep_theo="cpu", giam_dan=True, gioi_han=MAX_PROCESS)
                
                thong_tin["cpu_tong"] = min(100.0, thong_tin["cpu_tong"] + fake_cpu)
                thong_tin["ram_dung_mb"] += fake_ram
                if thong_tin["ram_tong_mb"] > 0:
                    thong_tin["ram_phan_tram"] = min(100.0, (thong_tin["ram_dung_mb"] / thong_tin["ram_tong_mb"]) * 100)
                
                ds.extend(self.tien_trinh_gia)
                ds.sort(key=lambda p: p.cpu, reverse=True)

                self.view.after(0, lambda: self._apply_data_to_ui(thong_tin, ds[:MAX_PROCESS+15]))
            except Exception as e:
                logger.error(f"Lỗi refresh TaskMgr: {e}")

        threading.Thread(target=worker_fetch_data, daemon=True).start()

    def _update_dashboard_ui(self, thong_tin):
        """Hàm dùng chung để vẽ thanh Progress Bar thật nhanh"""
        cpu_pct = thong_tin.get("cpu_tong", 0)
        ram_pct = thong_tin.get("ram_phan_tram", 0)
        ram_mb  = thong_tin.get("ram_dung_mb", 0)
        ram_total = thong_tin.get("ram_tong_mb", 1)

        self.view.lbl_cpu.config(text=f"CPU: {cpu_pct:.1f}%")
        self.view.lbl_ram.config(text=f"RAM: {ram_mb:.0f} MB / {ram_total:.0f} MB")

        self.view.bar_cpu["value"] = min(100, cpu_pct)
        self.view.bar_ram["value"] = min(100, ram_pct)

        cpu_style = "Danger" if cpu_pct > 80 else "Warn" if cpu_pct > 50 else "Safe"
        ram_style = "Danger" if ram_pct > 80 else "Warn" if ram_pct > 60 else "Safe"
        
        self.view.bar_cpu.config(style=f"{cpu_style}.Horizontal.TProgressbar")
        self.view.bar_ram.config(style=f"{ram_style}.Horizontal.TProgressbar")

    def _apply_data_to_ui(self, thong_tin, ds):
        try:
            self.thong_tin_hien_tai = thong_tin # Lưu lại để thao tác nhanh cho nút bấm
            self._update_dashboard_ui(thong_tin)
            ram_pct = thong_tin["ram_phan_tram"]

            # ── CƠ CHẾ OOM KILLER ──
            if ram_pct >= 95:
                if not self.da_canh_bao_oom:
                    self.da_canh_bao_oom = True
                    self.view.log_activity("🚨 NGUY HIỂM: RAM HỆ THỐNG VƯỢT MỨC 95%!", "error")
                    def show_popup():
                        messagebox.showwarning("Out Of Memory (OOM)", "Cảnh báo: Hệ thống sắp hết RAM!\nOOM Killer đang được kích hoạt để tìm và đóng ứng dụng ngốn RAM nhất.")
                    threading.Thread(target=show_popup, daemon=True).start()
                
                if self.tien_trinh_gia:
                    ung_dung_nang_nhat = max(self.tien_trinh_gia, key=lambda p: p.ram_mb)
                    self.tien_trinh_gia.remove(ung_dung_nang_nhat)
                    self.view.log_activity(f"💀 OOM KILLER ĐÃ BẮN BỎ: {ung_dung_nang_nhat.ten} (Giải phóng {ung_dung_nang_nhat.ram_mb:.0f} MB)", "error")
                    if self.view.tree.exists(str(ung_dung_nang_nhat.pid)):
                        self.view.tree.delete(str(ung_dung_nang_nhat.pid))
            
            elif ram_pct > 80:
                if not self.da_canh_bao_vang:
                    self.view.log_activity("⚠ Cảnh báo: RAM đang ở mức cao (>80%).", "warn")
                    self.da_canh_bao_vang = True
            else:
                self.da_canh_bao_oom = False
                self.da_canh_bao_vang = False
            # ────────────────────────────────────────────────

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
                values = (p.pid, p.ten, f"{p.cpu:.1f}%", f"{p.ram_mb:.0f} MB", p.trang_thai)
                bg_tag = "danger_cpu" if p.cpu > 70 else "warn_cpu" if p.cpu > 40 else ""
                if "[Ảo]" in p.ten:
                    bg_tag = "warn_cpu" 
                fg_tag = p.trang_thai.lower()

                if self.view.tree.exists(iid):
                    self.view.tree.item(iid, values=values, tags=(bg_tag, fg_tag))
                else:
                    self.view.tree.insert("", "end", iid=iid, values=values, tags=(bg_tag, fg_tag))
        except Exception as e:
            logger.error(f"Lỗi vẽ UI TaskMgr: {e}")