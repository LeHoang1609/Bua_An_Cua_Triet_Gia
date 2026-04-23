import tkinter as tk
from tkinter import ttk
import math
import random

# Màu chuẩn UI
COLORS = {
    "thinking": "#94a3b8",   # Xám
    "hungry": "#f59e0b",     # Cam
    "eating": "#22c55e"      # Xanh lá
}

class ViewTrietGia(tk.Frame):
    def __init__(self, parent, controller=None, **kw):
        super().__init__(parent, bg="#f8fafc", **kw)
        
        self.controller = controller
        self.running = False
        self.states = ["thinking"] * 5

        self._build_ui()
        self.update_ui(self.states)

    def _build_ui(self):
        # ==========================================
        # 1. TOP FRAME (Trạng thái & Chú thích)
        # ==========================================
        top_frame = tk.Frame(self, bg="#f8fafc")
        top_frame.pack(side="top", fill="x", padx=30, pady=10)

        self.lbl_status = tk.Label(top_frame, text="Trạng thái: Sẵn sàng", 
                                   font=("Segoe UI", 16, "bold"), fg="#2563eb", bg="#f8fafc")
        self.lbl_status.pack(side="left", anchor="n")

        legend_frame = tk.Frame(top_frame, bg="#f1f5f9", highlightbackground="#cbd5e1", 
                                highlightthickness=1, padx=10, pady=5)
        legend_frame.pack(side="right", anchor="n")

        self._create_legend_item(legend_frame, COLORS["thinking"], "Suy nghĩ (Xám)")
        self._create_legend_item(legend_frame, COLORS["hungry"], "Đang đói (Cam)")
        self._create_legend_item(legend_frame, COLORS["eating"], "Đang ăn (Xanh lá)")

        # ==========================================
        # 2. CENTER FRAME (Canvas)
        # ==========================================
        W, H = 800, 460
        canvas_container = tk.Frame(self, bg="#f8fafc")
        canvas_container.pack(expand=True)

        self.canvas = tk.Canvas(canvas_container, width=W, height=H, bg="#f8fafc", highlightthickness=0)
        self.canvas.pack()

        self.cx = W // 2
        self.cy = H // 2

        self.draw_table()
        self.draw_philosophers()
        self.draw_forks()

        # ==========================================
        # 3. BOTTOM FRAME (Control Panel)
        # ==========================================
        control_bg = "#e2e8f0"
        control = tk.Frame(self, bg=control_bg, padx=15, pady=15, 
                           highlightbackground="#cbd5e1", highlightthickness=1)
        control.pack(side="bottom", fill="x", padx=20, pady=20)

        row0 = tk.Frame(control, bg=control_bg)
        row0.pack(fill="x", pady=(0, 10))

        tk.Label(row0, text="Giải pháp:", bg=control_bg, font=("Segoe UI", 10)).pack(side="left", padx=(0, 10))
        
        # Thứ tự xuất hiện mới theo yêu cầu
        self.cbb_giaiphap = ttk.Combobox(row0, values=[
            "Không tránh deadlock", 
            "Semaphore", 
            "Monitor", 
            "Bất đối xứng"
        ], state="readonly", width=22, font=("Segoe UI", 10))
        self.cbb_giaiphap.current(0)
        self.cbb_giaiphap.pack(side="left", padx=(0, 30))
        self.cbb_giaiphap.bind("<<ComboboxSelected>>", self._on_combobox_change)

        tk.Button(row0, text="▶ Bắt đầu", width=12, command=self.start,
                  bg="#2563eb", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2").pack(side="left", padx=5)
        
        tk.Button(row0, text="⏸ Tạm dừng", width=12, command=self.stop,
                  bg="#f8fafc", fg="#1e293b", font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2").pack(side="left", padx=5)
        
        tk.Button(row0, text="🔄 Đặt lại", width=12, command=self.reset,
                  bg="#f8fafc", fg="#1e293b", font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2").pack(side="left", padx=5)

        row1 = tk.Frame(control, bg=control_bg)
        row1.pack(fill="x")

        tk.Label(row1, text="Mô tả giải pháp:", bg=control_bg, font=("Segoe UI", 10)).pack(side="left", padx=(0, 10))
        
        # Mô tả mặc định tương ứng với "Không tránh deadlock"
        self.lbl_desc = tk.Label(row1, text="Các triết gia tự do lấy đũa trái rồi đến đũa phải mà không có cơ chế điều phối. ⚠️ Dễ xảy ra deadlock.", 
                                 bg="white", fg="#334155", font=("Segoe UI", 10), anchor="w", padx=10, pady=4)
        self.lbl_desc.pack(side="left", fill="x", expand=True)

    def _create_legend_item(self, parent, color, text):
        f = tk.Frame(parent, bg="#f1f5f9")
        f.pack(anchor="w", pady=2)
        tk.Label(f, text="●", fg=color, bg="#f1f5f9", font=("Segoe UI", 16)).pack(side="left", padx=(0, 5))
        tk.Label(f, text=text, bg="#f1f5f9", fg="#475569", font=("Segoe UI", 10)).pack(side="left")

    def _on_combobox_change(self, event):
        val = self.cbb_giaiphap.get()

        if val == "Không tránh deadlock":
            self.lbl_desc.config(
                text="Các triết gia tự do lấy đũa trái rồi đến đũa phải mà không có cơ chế điều phối. ⚠️ Dễ xảy ra deadlock."
            )
        elif val == "Semaphore":
            self.lbl_desc.config(
                text="Dùng mảng semaphore, một triết gia chỉ được ăn khi cả hai đũa đều trống."
            )
        elif val == "Monitor":
            self.lbl_desc.config(
                text="Sử dụng Monitor (Condition variables) để quản lý và đánh thức triết gia."
            )
        elif val == "Bất đối xứng":
            self.lbl_desc.config(
                text="Triết gia lẻ lấy đũa trái trước, triết gia chẵn lấy đũa phải trước (phá chu kỳ chờ)."
            )

    def draw_table(self):
        R_table = 100
        self.canvas.create_oval(
            self.cx-R_table, self.cy-R_table, self.cx+R_table, self.cy+R_table,
            fill="#e2e8f0", outline="#cbd5e1", width=2
        )
        self.canvas.create_text(self.cx, self.cy, text="Bàn ăn", font=("Segoe UI", 16, "bold"), fill="#334155")

    def draw_philosophers(self):
        self.philos = []
        R_distance = 180  
        R_circle = 35
        for i in range(5):
            angle = 2 * math.pi * i / 5 - math.pi/2
            x = self.cx + R_distance * math.cos(angle)
            y = self.cy + R_distance * math.sin(angle)

            p = self.canvas.create_oval(x-R_circle, y-R_circle, x+R_circle, y+R_circle, 
                                        fill=COLORS["thinking"], outline="#334155", width=2)
            self.canvas.create_text(x, y, text=f"P{i}", font=("Segoe UI", 12, "bold"), fill="white")
            self.philos.append(p)

    def draw_forks(self):
        self.forks = []
        R_inner = 115  
        R_outer = 155  
        for i in range(5):
            angle = 2 * math.pi * i / 5 - math.pi/2 + math.pi/5
            x1 = self.cx + R_inner * math.cos(angle)
            y1 = self.cy + R_inner * math.sin(angle)
            x2 = self.cx + R_outer * math.cos(angle)
            y2 = self.cy + R_outer * math.sin(angle)

            f = self.canvas.create_line(x1, y1, x2, y2, width=6, fill="#cbd5e1", capstyle="round")
            self.forks.append(f)

    def start(self):
        if not self.running:
            self.running = True
            self.lbl_status.config(text="Trạng thái: Đang mô phỏng...", fg=COLORS["eating"])
            
            if self.controller:
                phuong_phap = self.cbb_giaiphap.get()
                self.controller.start_simulation(phuong_phap)
            else:
                self.loop_demo()

    def stop(self):
        self.running = False
        self.lbl_status.config(text="Trạng thái: Đã tạm dừng", fg=COLORS["hungry"])
        if self.controller:
            self.controller.stop_simulation()

    def reset(self):
        self.running = False
        self.lbl_status.config(text="Trạng thái: Sẵn sàng", fg="#2563eb")
        self.states = ["thinking"] * 5
        self.update_ui(self.states)
        if self.controller:
            self.controller.reset_simulation()

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
                self.canvas.itemconfig(self.forks[i], fill="#cbd5e1")

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