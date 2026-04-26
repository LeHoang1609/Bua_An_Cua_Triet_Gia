import tkinter as tk
from tkinter import ttk, messagebox
import random
import datetime

# ─────────────────────────────────────────────
# 🎨 BẢNG MÀU UI/UX CHUẨN
# ─────────────────────────────────────────────
BG_MAIN      = "#f8fafc"
BG_CARD      = "#ffffff"
PRIMARY      = "#2563eb"
TEXT_MAIN    = "#1e293b"
BORDER       = "#e2e8f0"

COLOR_RUNNING  = "#16a34a"
COLOR_WAITING  = "#d97706"
COLOR_BLOCKED  = "#6b7280"
COLOR_SLEEPING = "#3b82f6"

class ViewTaskManger(tk.Frame):
    def __init__(self, parent, controller=None, **kw):
        super().__init__(parent, bg=BG_MAIN, **kw)
        self.controller = controller
        self.running = True
        self.popup_shown = False
        self.blink_state = False
        self.refresh_delay = 500 
        
        self.search_query = tk.StringVar()
        self.search_query.trace_add("write", self._on_search_change)
        
        self.processes = [
            {"pid": 1042, "name": "System Services", "cpu": 0.5, "ram": 120.0, "status": "Running", "leak": False},
            {"pid": 3314, "name": "Google Chrome", "cpu": 15.4, "ram": 450.0, "status": "Running", "leak": False},
            {"pid": 5821, "name": "VS Code", "cpu": 4.2, "ram": 312.0, "status": "Sleeping", "leak": False},
            {"pid": 8920, "name": "Python Engine", "cpu": 25.0, "ram": 85.0, "status": "Waiting", "leak": False},
        ]

        self._init_styles()
        self._build_ui()
        self._initial_render()
        self.log_activity("Hệ thống đã sẵn sàng.", "success")
        self.animate_stats()

    def _init_styles(self):
        """Định nghĩa Style tường minh để giao diện đẹp và không lỗi"""
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Định nghĩa các Style cho Progressbar
        self.style.configure("Safe.Horizontal.TProgressbar", background="#22c55e", thickness=20)
        self.style.configure("Warn.Horizontal.TProgressbar", background="#f59e0b", thickness=20)
        self.style.configure("Danger.Horizontal.TProgressbar", background="#ef4444", thickness=20)
        self.style.configure("Critical.Horizontal.TProgressbar", background="#991b1b", thickness=20)

        # Style cho Treeview
        self.style.configure("Custom.Treeview", rowheight=38, font=("Segoe UI", 10), borderwidth=0)
        self.style.map("Custom.Treeview", background=[('selected', '#dbeafe')], foreground=[('selected', PRIMARY)])

    def _build_ui(self):
        # --- DASHBOARD ---
        dash = tk.Frame(self, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1)
        dash.pack(side="top", fill="x", padx=20, pady=(20, 10))
        tk.Label(dash, text="📊 QUẢN TRỊ TÀI NGUYÊN HỆ THỐNG", font=("Segoe UI", 12, "bold"), fg=PRIMARY, bg=BG_CARD).pack(anchor="w", padx=20, pady=(15, 5))
        
        stats_frame = tk.Frame(dash, bg=BG_CARD)
        stats_frame.pack(fill="x", padx=20, pady=(0, 20))

        # CPU
        box_cpu = tk.Frame(stats_frame, bg=BG_CARD)
        box_cpu.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.lbl_cpu = tk.Label(box_cpu, text="CPU Usage: 0%", font=("Segoe UI", 10, "bold"), bg=BG_CARD)
        self.lbl_cpu.pack(anchor="w")
        self.bar_cpu = ttk.Progressbar(box_cpu, orient="horizontal", mode="determinate", style="Safe.Horizontal.TProgressbar")
        self.bar_cpu.pack(fill="x", pady=5)

        # RAM
        box_ram = tk.Frame(stats_frame, bg=BG_CARD)
        box_ram.pack(side="left", fill="x", expand=True, padx=(10, 0))
        self.lbl_ram = tk.Label(box_ram, text="RAM Usage: 0 MB", font=("Segoe UI", 10, "bold"), bg=BG_CARD)
        self.lbl_ram.pack(anchor="w")
        self.bar_ram = ttk.Progressbar(box_ram, orient="horizontal", mode="determinate", style="Safe.Horizontal.TProgressbar")
        self.bar_ram.pack(fill="x", pady=5)

        # --- CONTENT ---
        main_content = tk.Frame(self, bg=BG_MAIN)
        main_content.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Sidebar (Logs)
        side = tk.Frame(main_content, bg=BG_CARD, width=260, highlightbackground=BORDER, highlightthickness=1)
        side.pack(side="right", fill="y", padx=(15, 0))
        side.pack_propagate(False)

        tk.Label(side, text="⚙️ ĐIỀU KHIỂN", font=("Segoe UI", 11, "bold"), bg=BG_CARD).pack(pady=15)
        self.btn_kill = tk.Button(side, text="❌ End Task", bg="#fca5a5", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", state="disabled", command=self.kill_selected)
        self.btn_kill.pack(fill="x", padx=20, pady=5, ipady=8)
        tk.Button(side, text="➕ New Task", bg="#22c55e", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", command=self.create_task).pack(fill="x", padx=20, pady=5, ipady=8)

        tk.Label(side, text="📝 SYSTEM LOGS", font=("Segoe UI", 9, "bold"), fg="#64748b", bg=BG_CARD).pack(anchor="w", padx=20, pady=(20, 5))
        self.log_box = tk.Text(side, font=("Consolas", 9), bg="#f8fafc", relief="flat", state="disabled")
        self.log_box.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.log_box.tag_configure("success", foreground="#16a34a")
        self.log_box.tag_configure("error", foreground="#ef4444")
        self.log_box.tag_configure("warn", foreground="#d97706")

        # Table
        table_card = tk.Frame(main_content, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1)
        table_card.pack(side="left", fill="both", expand=True)
        
        search_f = tk.Frame(table_card, bg=BG_CARD, pady=10, padx=15)
        search_f.pack(fill="x")
        self.ent_search = tk.Entry(search_f, textvariable=self.search_query, font=("Segoe UI", 10), width=25)
        self.ent_search.pack(side="right", padx=10)
        tk.Label(search_f, text="Tìm kiếm:", bg=BG_CARD).pack(side="right")

        self.tree = ttk.Treeview(table_card, columns=("PID", "Name", "CPU", "RAM", "Status"), show="headings", style="Custom.Treeview")
        for col in ("PID", "Name", "CPU", "RAM", "Status"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center" if col != "Name" else "w")

        # Tags màu
        self.tree.tag_configure("running", foreground="#16a34a")
        self.tree.tag_configure("waiting", foreground="#d97706")
        self.tree.tag_configure("blocked", foreground="#6b7280")
        self.tree.tag_configure("sleeping", foreground="#3b82f6")
        self.tree.tag_configure("warn_cpu", background="#fee2e2")
        self.tree.tag_configure("danger_cpu", background="#fecaca")
        
        self.tree.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.tree.bind("<<TreeviewSelect>>", self._on_select_change)

    # ==========================================
    # LOGIC (Đã Fix Lỗi RAM Cập Nhật & Cảnh Báo)
    # ==========================================
    def log_activity(self, msg, tag="info"):
        t = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_box.config(state="normal")
        self.log_box.insert("1.0", f"[{t}] {msg}\n", tag)
        self.log_box.config(state="disabled")

    def kill_selected(self):
        sel = self.tree.selection()
        if not sel: return
        pid = self.tree.item(sel[0])['values'][0]
        self.processes = [p for p in self.processes if p["pid"] != pid]
        self.tree.delete(sel[0])
        self.log_activity(f"Killed PID: {pid}", "error")

    def create_task(self):
        pid = random.randint(1000, 9999)
        is_leak = random.random() < 0.2
        name = "LeakApp.exe" if is_leak else random.choice(["Chrome.exe", "Spotify.exe", "Game.exe"])
        new_p = {"pid": pid, "name": name, "cpu": 5.0, "ram": random.uniform(200, 500), "status": "Running", "leak": is_leak}
        self.processes.append(new_p)
        self.tree.insert("", "end", iid=str(pid), values=(pid, name, "5%", "0 MB", "Running"))
        self.log_activity(f"Started: {name} {'(⚠️ LEAK)' if is_leak else ''}", "success")

    def _on_select_change(self, _):
        if self.tree.selection(): self.btn_kill.config(state="normal", bg="#ef4444")
        else: self.btn_kill.config(state="disabled", bg="#fca5a5")

    def _on_search_change(self, *args):
        q = self.search_query.get().lower()
        for p in self.processes:
            iid = str(p["pid"])
            if self.tree.exists(iid):
                if q in p["name"].lower() or q in iid: self.tree.reattach(iid, "", "end")
                else: self.tree.detach(iid)

    def _initial_render(self):
        for p in self.processes:
            self.tree.insert("", "end", iid=str(p["pid"]), values=(p["pid"], p["name"], "0%", "0 MB", p["status"]))

    def animate_stats(self):
        if not self.running: return
        t_cpu, t_ram = 0, 0
        throttle = 0.6 if sum(p["cpu"] for p in self.processes) > 90 else 1.0

        for p in self.processes:
            p["cpu"] = max(0.1, round(p["cpu"] + random.uniform(-5, 5) * throttle, 1))
            if p["leak"]: p["ram"] += random.uniform(30, 80)
            else: p["ram"] = max(10, round(p["ram"] + random.uniform(-5, 5), 1))
            t_cpu += p["cpu"]; t_ram += p["ram"]

            iid = str(p["pid"])
            if self.tree.exists(iid):
                bg_tag = "danger_cpu" if p["cpu"] > 70 else ("warn_cpu" if p["cpu"] > 40 else "")
                fg_tag = p["status"].lower()
                self.tree.item(iid, values=(p["pid"], p["name"], f"{p['cpu']}%", f"{p['ram']:.1f} MB", p["status"]), tags=(bg_tag, fg_tag))

        # Update Dashboards
        t_cpu = min(100, round(t_cpu, 1))
        self.lbl_cpu.config(text=f"CPU: {t_cpu}%")
        self.bar_cpu['value'] = t_cpu
        self.bar_cpu.config(style=f"{'Danger' if t_cpu > 80 else ('Warn' if t_cpu > 50 else 'Safe')}.Horizontal.TProgressbar")

        # FIX RAM: Cho phép tính ram_p vượt quá 100 để điều kiện If/Else hoạt động
        ram_p = (t_ram / 8192) * 100
        self.lbl_ram.config(text=f"RAM: {t_ram:.1f} MB / 8192 MB")
        
        # Thanh giao diện chỉ giới hạn hiển thị ở 100% để tránh lỗi UI
        self.bar_ram['value'] = min(100, ram_p)

        if ram_p > 100:
            self.refresh_delay = 1500 # SYSTEM LAG
            self.blink_state = not self.blink_state
            style_r = "Danger" if self.blink_state else "Critical"
            
            # Chỉ hiện popup 1 lần để tránh spam
            if not self.popup_shown:
                self.popup_shown = True
                messagebox.showwarning("Cảnh báo Hệ Thống", "Cảnh báo: Bộ nhớ RAM đã vượt quá 100%!\nChuẩn bị kích hoạt OOM Killer để giải phóng bộ nhớ.")

            if ram_p > 115:
                # Tìm tiến trình ngốn RAM nhất và tắt nó đi
                if self.processes:  # Đảm bảo danh sách không trống
                    biggest = max(self.processes, key=lambda x: x["ram"])
                    self.log_activity(f"💀 OOM Killer: Terminated {biggest['name']}", "error")
                    self.processes.remove(biggest)
                    if self.tree.exists(str(biggest["pid"])):
                        self.tree.delete(str(biggest["pid"]))
        elif ram_p > 80:
            self.refresh_delay = 800
            style_r = "Warn"
            self.popup_shown = False # Reset popup khi hệ thống đã bớt gắt
        else:
            self.refresh_delay = 500
            style_r = "Safe"
            self.popup_shown = False # Reset popup

        self.bar_ram.config(style=f"{style_r}.Horizontal.TProgressbar")
        self.after(self.refresh_delay, self.animate_stats)

# Khởi chạy chương trình (Thêm đoạn này ở cuối để test độc lập)
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Task Manager Demo")
    root.geometry("900x600")
    app = ViewTaskManger(root)
    app.pack(fill="both", expand=True)
    root.mainloop()