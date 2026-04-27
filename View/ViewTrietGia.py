import tkinter as tk
from tkinter import ttk
import math
import random

# ─────────────────────────────────────────────
# 🎨 BẢNG MÀU
# ─────────────────────────────────────────────
STATE_COLORS = {
    "thinking": "#3498db",
    "hungry":   "#f39c12",
    "eating":   "#2ecc71",
    "blocked":  "#e74c3c",
    "starving": "#8e44ad"
}

STATE_TEXTS = {
    "thinking": "Thinking",
    "hungry":   "Hungry",
    "eating":   "Eating",
    "blocked":  "Blocked",
    "starving": "Starving"
}

BG_MAIN      = "#f5f6fa"
BG_CARD      = "#ffffff"
BORDER_COLOR = "#dcdde1"


class ViewTrietGia(tk.Frame):
    def __init__(self, parent, controller=None, **kw):
        super().__init__(parent, bg=BG_MAIN, **kw)

        self.controller  = controller
        self.running     = False
        self.states      = ["thinking"] * 5
        self.philo_ovals = []
        self.philo_texts = []
        self.forks       = []

        self._build_ui()
        self.update_snapshot(self.states, [0] * 5, [0] * 5, 0)

    def _build_ui(self):
        # ── CONTROL PANEL (dưới cùng) ───────────────────────────────────
        control_frame = tk.Frame(self, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1)
        control_frame.pack(side="bottom", fill="x", padx=15, pady=15)

        row_ctrl = tk.Frame(control_frame, bg=BG_CARD, pady=10, padx=15)
        row_ctrl.pack(fill="x")

        tk.Label(row_ctrl, text="Giải pháp:", bg=BG_CARD, font=("Segoe UI", 10, "bold"), fg="#2f3542").pack(side="left", padx=(0, 10))
        self.cbb_giaiphap = ttk.Combobox(
            row_ctrl,
            values=["Không tránh deadlock", "Semaphore", "Monitor", "Bất đối xứng"],
            state="readonly", width=22
        )
        self.cbb_giaiphap.current(0)
        self.cbb_giaiphap.pack(side="left", padx=(0, 20))
        self.cbb_giaiphap.bind("<<ComboboxSelected>>", self._on_combobox_change)

        self.btn_auto  = tk.Button(row_ctrl, text="▶ Auto",  width=10, command=self.start,
                                   bg="#3498db", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2")
        self.btn_buoc  = tk.Button(row_ctrl, text="⏭ Bước",  width=10, command=self.step_forward,
                                   bg="#2ecc71", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2")
        self.btn_dung  = tk.Button(row_ctrl, text="⏸ Dừng",  width=10, command=self.stop,
                                   bg="#f5f6fa", fg="#2f3542", font=("Segoe UI", 10, "bold"), relief="flat",
                                   highlightbackground=BORDER_COLOR, highlightthickness=1, cursor="hand2")
        self.btn_reset = tk.Button(row_ctrl, text="🔄 Reset", width=10, command=self.reset,
                                   bg="#f5f6fa", fg="#2f3542", font=("Segoe UI", 10, "bold"), relief="flat",
                                   highlightbackground=BORDER_COLOR, highlightthickness=1, cursor="hand2")

        self.btn_auto.pack(side="left",  padx=5)
        self.btn_buoc.pack(side="left",  padx=5)
        self.btn_dung.pack(side="left",  padx=5)
        self.btn_reset.pack(side="left", padx=5)

        self.lbl_status = tk.Label(row_ctrl, text="Trạng thái: Sẵn sàng",
                                   font=("Segoe UI", 12, "bold"), fg="#3498db", bg=BG_CARD)
        self.lbl_status.pack(side="right", padx=10)

        # ── MAIN VIEW ───────────────────────────────────────────────────
        main_view = tk.Frame(self, bg=BG_MAIN)
        main_view.pack(side="top", fill="both", expand=True, padx=15, pady=(15, 0))

        # ── INFO PANEL (phải) ────────────────────────────────────────────
        info_panel = tk.Frame(main_view, bg=BG_CARD, width=320,
                              highlightbackground=BORDER_COLOR, highlightthickness=1)
        info_panel.pack(side="right", fill="y", padx=(10, 0))
        info_panel.pack_propagate(False)

        tk.Label(info_panel, text="📊 BẢNG THỐNG KÊ",
                 font=("Segoe UI", 11, "bold"), bg=BG_CARD, fg="#2c3e50").pack(pady=(15, 10))

        table_container = tk.Frame(info_panel, bg=BG_CARD)
        table_container.pack(fill="x", padx=10)

        scroll_y = ttk.Scrollbar(table_container, orient="vertical")
        scroll_y.pack(side="right", fill="y")

        self.tree_stats = ttk.Treeview(
            table_container,
            columns=("ID", "Wait", "Skip"),
            show="headings", height=6,
            yscrollcommand=scroll_y.set
        )
        scroll_y.config(command=self.tree_stats.yview)

        self.tree_stats.heading("ID",   text="P")
        self.tree_stats.heading("Wait", text="TG Chờ")
        self.tree_stats.heading("Skip", text="Bị cướp")

        self.tree_stats.column("ID",   width=50,  anchor="center")
        self.tree_stats.column("Wait", width=100, anchor="center")
        self.tree_stats.column("Skip", width=100, anchor="center")
        self.tree_stats.pack(side="left", fill="x", expand=True)

        # ── Deadlock counter ─────────────────────────────────────────────
        tk.Frame(info_panel, bg=BORDER_COLOR, height=1).pack(fill="x", padx=10, pady=(12, 8))

        deadlock_row = tk.Frame(info_panel, bg=BG_CARD)
        deadlock_row.pack(fill="x", padx=15, pady=(0, 8))
        tk.Label(deadlock_row, text="💀 Deadlocks phát hiện:",
                 font=("Segoe UI", 10, "bold"), bg=BG_CARD, fg="#2c3e50").pack(side="left")
        self.lbl_deadlock = tk.Label(deadlock_row, text="0",
                                     font=("Segoe UI", 12, "bold"), bg=BG_CARD, fg="#e74c3c")
        self.lbl_deadlock.pack(side="right")

        # ── Mô tả thuật toán ─────────────────────────────────────────────
        tk.Frame(info_panel, bg=BORDER_COLOR, height=1).pack(fill="x", padx=10, pady=(0, 10))

        tk.Label(info_panel, text="📌 Mô tả thuật toán:",
                 font=("Segoe UI", 10, "bold"), bg=BG_CARD, fg="#2c3e50", anchor="w").pack(fill="x", padx=15)

        self.lbl_desc = tk.Label(info_panel, text="", bg=BG_CARD, fg="#475569",
                                 font=("Segoe UI", 10), justify="left", wraplength=280, anchor="nw")
        self.lbl_desc.pack(fill="both", expand=True, padx=15, pady=5)
        self._on_combobox_change(None)

        # ── SIMULATION PANEL (trái/giữa) ─────────────────────────────────
        sim_panel = tk.Frame(main_view, bg=BG_CARD,
                             highlightbackground=BORDER_COLOR, highlightthickness=1)
        sim_panel.pack(side="left", fill="both", expand=True)

        legend_frame = tk.Frame(sim_panel, bg=BG_MAIN, pady=8)
        legend_frame.pack(fill="x")

        legends = [
            ("🔵 Thinking", STATE_COLORS["thinking"]),
            ("🟠 Hungry",   STATE_COLORS["hungry"]),
            ("🟢 Eating",   STATE_COLORS["eating"]),
            ("🔴 Blocked",  STATE_COLORS["blocked"]),
            ("🟣 Starving", STATE_COLORS["starving"]),
        ]
        legend_inner = tk.Frame(legend_frame, bg=BG_MAIN)
        legend_inner.pack(anchor="center")
        for text, color in legends:
            tk.Label(legend_inner, text=text, fg=color, bg=BG_MAIN,
                     font=("Segoe UI", 10, "bold")).pack(side="left", padx=10)

        self.canvas = tk.Canvas(sim_panel, bg=BG_CARD, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        self.canvas.bind("<Configure>", self._on_canvas_resize)

    def _on_canvas_resize(self, event):
        # CHẶN VÒNG LẶP VẼ VÔ TẬN GÂY LAG UI
        if hasattr(self, '_last_w') and self._last_w == event.width and getattr(self, '_last_h', 0) == event.height:
            return  
        self._last_w = event.width
        self._last_h = event.height

        self.canvas.delete("all")
        self.cx = event.width  // 2
        self.cy = event.height // 2
        self.draw_table()
        self.draw_philosophers()
        self.draw_forks()
        self.update_snapshot(self.states, [0] * 5, [0] * 5, 0)

    def _on_combobox_change(self, event):
        val = self.cbb_giaiphap.get()
        descs = {
            "Không tránh deadlock": (
                "- Triết gia tự do lấy đũa trái rồi đến đũa phải.\n"
                "- Không có cơ chế điều phối.\n"
                "- ⚠️ Rất dễ xảy ra Deadlock và Starvation."
            ),
            "Semaphore": (
                "- Giới hạn tối đa N-1 người ngồi cùng lúc.\n"
                "- Quản lý bằng Semaphore (biến đếm).\n"
                "- Tránh được deadlock hoàn toàn."
            ),
            "Monitor": (
                "- Sử dụng Condition Variable (threading.Condition).\n"
                "- Triết gia chỉ được lấy đũa khi CẢ HAI đũa đều rảnh.\n"
                "- Đảm bảo tính toàn vẹn, không deadlock."
            ),
            "Bất đối xứng": (
                "- Phá vỡ chu trình chờ chéo.\n"
                "- Luôn lấy đũa có số nhỏ hơn trước.\n"
                "- Không bao giờ xảy ra deadlock."
            ),
        }
        self.lbl_desc.config(text=f"Giải pháp: {val}\n\n{descs.get(val, '')}")

    def draw_table(self):
        R = min(self.cx, self.cy) * 0.35
        self.canvas.create_oval(
            self.cx - R, self.cy - R, self.cx + R, self.cy + R,
            fill="#ecf0f1", outline="#bdc3c7", width=3
        )
        self.canvas.create_text(self.cx, self.cy, text="Bàn ăn",
                                font=("Segoe UI", 16, "bold"), fill="#2c3e50")

    def draw_philosophers(self):
        self.philo_ovals = []
        self.philo_texts = []
        R_dist = min(self.cx, self.cy) * 0.65
        R_node = 45

        self.tree_stats.delete(*self.tree_stats.get_children())

        for i in range(5):
            angle = 2 * math.pi * i / 5 - math.pi / 2
            x = self.cx + R_dist * math.cos(angle)
            y = self.cy + R_dist * math.sin(angle)

            p_oval = self.canvas.create_oval(
                x - R_node, y - R_node, x + R_node, y + R_node,
                fill=STATE_COLORS["thinking"], outline="#2c3e50", width=2
            )
            p_text = self.canvas.create_text(
                x, y,
                text=f"P{i}\n({STATE_TEXTS['thinking']})",
                font=("Segoe UI", 10, "bold"), fill="white", justify="center"
            )
            self.philo_ovals.append(p_oval)
            self.philo_texts.append(p_text)
            self.tree_stats.insert("", "end", iid=f"p{i}", values=(f"P{i}", "0", "0"))

    def draw_forks(self):
        self.forks = []
        R_in  = min(self.cx, self.cy) * 0.40
        R_out = min(self.cx, self.cy) * 0.55
        for i in range(5):
            angle = 2 * math.pi * i / 5 - math.pi / 2 + math.pi / 5
            x1 = self.cx + R_in  * math.cos(angle)
            y1 = self.cy + R_in  * math.sin(angle)
            x2 = self.cx + R_out * math.cos(angle)
            y2 = self.cy + R_out * math.sin(angle)
            f  = self.canvas.create_line(x1, y1, x2, y2, width=8,
                                         fill="#bdc3c7", capstyle="round")
            self.forks.append(f)

    def update_snapshot(self, states, wait_times, stolen_counts, so_deadlock=0):
        """Cập nhật toàn bộ UI từ snapshot mới nhất."""
        if not hasattr(self, 'philo_ovals') or len(self.philo_ovals) == 0:
            return

        self.states = states

        for i, state in enumerate(states):
            color       = STATE_COLORS.get(state, STATE_COLORS["thinking"])
            status_name = STATE_TEXTS.get(state, "Thinking")

            self.canvas.itemconfig(self.philo_ovals[i], fill=color)
            self.canvas.itemconfig(self.philo_texts[i],
                                   text=f"P{i}\n({status_name})")

            if self.tree_stats.exists(f"p{i}"):
                self.tree_stats.item(f"p{i}", values=(
                    f"P{i}",
                    wait_times[i],
                    stolen_counts[i]
                ))

        # --- BƯỚC 1: RESET TẤT CẢ ĐŨA VỀ MÀU XÁM ---
        for i in range(5):
            self.canvas.itemconfig(self.forks[i], fill="#bdc3c7")

        # --- BƯỚC 2: TÔ XANH 2 ĐŨA CHO NHỮNG NGƯỜI ĐANG ĂN ---
        for i in range(5):
            if states[i] == "eating":
                self.canvas.itemconfig(self.forks[i], fill=STATE_COLORS["eating"])
                self.canvas.itemconfig(self.forks[(i - 1) % 5], fill=STATE_COLORS["eating"])
        # ------------------------------------------

        # Cập nhật bộ đếm deadlock
        self.lbl_deadlock.config(text=str(so_deadlock))

    # ── CONTROL ──────────────────────────────────────────────────────────

    def _set_buttons(self, running: bool):
        """Quản lý trạng thái enable/disable các nút."""
        if running:
            self.btn_auto.config( state="disabled", bg="#a0c4e8")
            self.btn_buoc.config( state="disabled", bg="#a0dbb8")
            self.btn_dung.config( state="normal")
            self.btn_reset.config(state="normal")
        else:
            self.btn_auto.config( state="normal",   bg="#3498db")
            self.btn_buoc.config( state="normal",   bg="#2ecc71")
            self.btn_dung.config( state="disabled")
            self.btn_reset.config(state="normal")

    def start(self):
        if not self.running:
            self.running = True
            self._set_buttons(True)
            self.lbl_status.config(text="Trạng thái: Đang chạy (Auto)", fg="#3498db")
            if self.controller:
                self.controller.start_simulation(self.cbb_giaiphap.get())
            else:
                self.loop_demo()

    def step_forward(self):
        self.running = False
        self.lbl_status.config(text="Trạng thái: Chạy từng bước", fg="#2ecc71")
        if self.controller:
            self.controller.step_simulation(self.cbb_giaiphap.get())
        else:
            self.single_step_demo()

    def stop(self):
        self.running = False
        self._set_buttons(False)
        self.lbl_status.config(text="Trạng thái: Đã tạm dừng", fg="#e74c3c")
        if self.controller:
            self.controller.stop_simulation()

    def reset(self):
        self.running = False
        self._set_buttons(False)
        self.lbl_status.config(text="Trạng thái: Sẵn sàng", fg="#3498db")
        if self.controller:
            self.controller.reset_simulation()
        self.update_snapshot(["thinking"] * 5, [0] * 5, [0] * 5, 0)

    # ── DEMO (không có controller) ────────────────────────────────────────

    def single_step_demo(self):
        idx       = random.randint(0, 4)
        new_state = random.choice(list(STATE_COLORS.keys()))
        self.states[idx] = new_state
        waits  = [random.randint(0, 5) if s != "eating" else 0 for s in self.states]
        skips  = [random.randint(0, 3) for _ in range(5)]
        self.update_snapshot(self.states, waits, skips, random.randint(0, 5))

    def loop_demo(self):
        if not self.running:
            return
        self.single_step_demo()
        self.after(1500, self.loop_demo)