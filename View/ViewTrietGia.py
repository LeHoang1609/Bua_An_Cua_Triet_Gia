import tkinter as tk
from tkinter import ttk
import math
import random

# ─────────────────────────────────────────────
#  BẢNG MÀU ĐÃ ĐƯỢC "VỰC DẬY" (CONTRAST FIX)
# ─────────────────────────────────────────────
COLORS = {
    "thinking": "#64748b",   # Slate đậm - nhìn trí tuệ hơn
    "hungry":   "#f59e0b",   # Cam hổ phách
    "eating":   "#22c55e"    # Xanh lục tươi
}
COLOR_FORK_IDLE = "#94a3b8"  # Đũa đậm hơn, dễ quan sát
COLOR_TABLE_BG  = "#cbd5e1"  # Bàn ăn đậm hơn chút để có khối
COLOR_CANVAS_BG = "#f8fafc"

class ViewTrietGia(tk.Frame):
    def __init__(self, parent, controller=None, **kw):
        super().__init__(parent, bg=COLOR_CANVAS_BG, **kw)
        
        self.controller = controller
        self.running = False
        self.states = ["thinking"] * 5

        self._build_ui()
        self.update_ui(self.states)

    def _build_ui(self):
        # 1. TOP FRAME
        top_frame = tk.Frame(self, bg=COLOR_CANVAS_BG)
        top_frame.pack(side="top", fill="x", padx=30, pady=10)

        self.lbl_status = tk.Label(top_frame, text="Trạng thái: Sẵn sàng", 
                                   font=("Segoe UI", 16, "bold"), fg="#2563eb", bg=COLOR_CANVAS_BG)
        self.lbl_status.pack(side="left", anchor="n")

        legend_frame = tk.Frame(top_frame, bg="#ffffff", highlightbackground="#cbd5e1", 
                                highlightthickness=1, padx=12, pady=8)
        legend_frame.pack(side="right", anchor="n")

        self._create_legend_item(legend_frame, COLORS["thinking"], "Suy nghĩ")
        self._create_legend_item(legend_frame, COLORS["hungry"], "Đang đói")
        self._create_legend_item(legend_frame, COLORS["eating"], "Đang ăn")

        # 2. CENTER FRAME (Canvas - Fix rời rạc)
        W, H = 800, 480
        canvas_container = tk.Frame(self, bg=COLOR_CANVAS_BG)
        canvas_container.pack(expand=True)

        self.canvas = tk.Canvas(canvas_container, width=W, height=H, bg=COLOR_CANVAS_BG, highlightthickness=0)
        self.canvas.pack()

        self.cx, self.cy = W // 2, H // 2

        self.draw_table()
        self.draw_philosophers()
        self.draw_forks()

        # 3. BOTTOM FRAME (Control Panel - Thêm điểm nhấn)
        control_bg = "#f1f5f9" # Nền hơi đậm hơn canvas để phân lớp
        control = tk.Frame(self, bg=control_bg, padx=20, pady=15, 
                           highlightbackground="#cbd5e1", highlightthickness=2)
        control.pack(side="bottom", fill="x", padx=25, pady=20)

        row0 = tk.Frame(control, bg=control_bg)
        row0.pack(fill="x", pady=(0, 10))

        tk.Label(row0, text="Giải pháp:", bg=control_bg, font=("Segoe UI", 10, "bold"), fg="#334155").pack(side="left", padx=(0, 10))
        
        self.cbb_giaiphap = ttk.Combobox(row0, values=[
            "Không tránh deadlock", 
            "Semaphore", 
            "Monitor", 
            "Bất đối xứng"
        ], state="readonly", width=22, font=("Segoe UI", 10))
        self.cbb_giaiphap.current(0)
        self.cbb_giaiphap.pack(side="left", padx=(0, 30))
        self.cbb_giaiphap.bind("<<ComboboxSelected>>", self._on_combobox_change)

        # Style cho Button đồng bộ
        btn_start = tk.Button(row0, text="▶ Bắt đầu", width=12, command=self.start,
                             bg="#2563eb", fg="white", font=("Segoe UI", 10, "bold"), 
                             relief="flat", cursor="hand2")
        btn_start.pack(side="left", padx=5)
        
        for text, cmd in [("⏸ Tạm dừng", self.stop), ("🔄 Đặt lại", self.reset)]:
            tk.Button(row0, text=text, width=12, command=cmd,
                      bg="#ffffff", fg="#1e293b", font=("Segoe UI", 10, "bold"), 
                      relief="flat", highlightbackground="#cbd5e1", highlightthickness=1,
                      cursor="hand2").pack(side="left", padx=5)

        row1 = tk.Frame(control, bg=control_bg)
        row1.pack(fill="x")

        tk.Label(row1, text="Mô tả giải pháp:", bg=control_bg, font=("Segoe UI", 10, "bold"), fg="#334155").pack(side="left", padx=(0, 10))
        self.lbl_desc = tk.Label(row1, text="Các triết gia tự do lấy đũa trái rồi đến đũa phải mà không có cơ chế điều phối. ⚠️ Dễ xảy ra deadlock.", 
                                 bg="white", fg="#475569", font=("Segoe UI", 10), anchor="w", padx=10, pady=6,
                                 highlightbackground="#cbd5e1", highlightthickness=1)
        self.lbl_desc.pack(side="left", fill="x", expand=True)

    def _create_legend_item(self, parent, color, text):
        f = tk.Frame(parent, bg="#ffffff")
        f.pack(anchor="w", pady=2)
        tk.Label(f, text="●", fg=color, bg="#ffffff", font=("Segoe UI", 16)).pack(side="left", padx=(0, 5))
        tk.Label(f, text=text, bg="#ffffff", fg="#475569", font=("Segoe UI", 10, "bold")).pack(side="left")

    def _on_combobox_change(self, event):
        val = self.cbb_giaiphap.get()
        descs = {
            "Không tránh deadlock": "Các triết gia tự do lấy đũa trái rồi đến đũa phải mà không có cơ chế điều phối. ⚠️ Dễ xảy ra deadlock.",
            "Semaphore": "Dùng mảng semaphore, một triết gia chỉ được ăn khi cả hai đũa đều trống.",
            "Monitor": "Sử dụng Monitor (Condition variables) để quản lý và đánh thức triết gia.",
            "Bất đối xứng": "Triết gia lẻ lấy đũa trái trước, triết gia chẵn lấy đũa phải trước (phá chu kỳ chờ)."
        }
        self.lbl_desc.config(text=descs.get(val, ""))

    def draw_table(self):
        R_table = 100
        self.canvas.create_oval(
            self.cx-R_table, self.cy-R_table, self.cx+R_table, self.cy+R_table,
            fill=COLOR_TABLE_BG, outline="#94a3b8", width=3
        )
        self.canvas.create_text(self.cx, self.cy, text="Bàn ăn", font=("Segoe UI", 16, "bold"), fill="#1e293b")

    def draw_philosophers(self):
        self.philos = []
        R_distance = 200  # Rút ngắn từ 230 -> 200 (Fix rời rạc)
        R_circle = 38     # Tăng size nhẹ cho nổi bật
        for i in range(5):
            angle = 2 * math.pi * i / 5 - math.pi/2
            x, y = self.cx + R_distance * math.cos(angle), self.cy + R_distance * math.sin(angle)
            p = self.canvas.create_oval(x-R_circle, y-R_circle, x+R_circle, y+R_circle, 
                                        fill=COLORS["thinking"], outline="#1e293b", width=2)
            self.canvas.create_text(x, y, text=f"P{i}", font=("Segoe UI", 12, "bold"), fill="white")
            self.philos.append(p)

    def draw_forks(self):
        self.forks = []
        R_inner, R_outer = 115, 165 # Chỉnh lại khoảng cách đũa cho khớp R mới
        for i in range(5):
            angle = 2 * math.pi * i / 5 - math.pi/2 + math.pi/5
            x1, y1 = self.cx + R_inner * math.cos(angle), self.cy + R_inner * math.sin(angle)
            x2, y2 = self.cx + R_outer * math.cos(angle), self.cy + R_outer * math.sin(angle)
            f = self.canvas.create_line(x1, y1, x2, y2, width=7, fill=COLOR_FORK_IDLE, capstyle="round")
            self.forks.append(f)

    def start(self):
        if not self.running:
            self.running = True
            self.lbl_status.config(text="Trạng thái: Đang mô phỏng...", fg="#16a34a")
            if self.controller:
                self.controller.start_simulation(self.cbb_giaiphap.get())
            else: self.loop_demo()

    def stop(self):
        self.running = False
        self.lbl_status.config(text="Trạng thái: Đã tạm dừng", fg="#dc2626")

    def reset(self):
        self.running = False
        self.lbl_status.config(text="Trạng thái: Sẵn sàng", fg="#2563eb")
        self.states = ["thinking"] * 5
        self.update_ui(self.states)

    def update_snapshot(self, states):
        self.states = states
        self.update_ui(self.states)

    def update_ui(self, states):
        for i, state in enumerate(states):
            self.canvas.itemconfig(self.philos[i], fill=COLORS[state])
        for i in range(5):
            if states[i] == "eating":
                self.canvas.itemconfig(self.forks[i], fill=COLORS["eating"])
                self.canvas.itemconfig(self.forks[(i-1)%5], fill=COLORS["eating"])
            else:
                self.canvas.itemconfig(self.forks[i], fill=COLOR_FORK_IDLE)

    def loop_demo(self):
        if not self.running: return
        new_states = ["thinking"] * 5
        for i in range(5):
            rand = random.random()
            if rand < 0.25: new_states[i] = "eating"
            elif rand < 0.6: new_states[i] = "hungry"
        for i in range(5):
            if new_states[i] == "eating" and new_states[(i+1)%5] == "eating":
                new_states[(i+1)%5] = "hungry"
        self.update_snapshot(new_states)
        self.after(600, self.loop_demo)