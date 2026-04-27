import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# ─────────────────────────────────────────────
#  PALETTE MÀU CHUẨN & HIỆN ĐẠI
# ─────────────────────────────────────────────
BG_MAIN    = "#f8fafc"
BG_CARD    = "#ffffff"
TEXT_MAIN  = "#1e293b"
TEXT_SUB   = "#475569"
PRIMARY    = "#2563eb"
BORDER     = "#cbd5e1"

# Dải màu tươi sáng, độ tương phản cao
GANTT_COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#ec4899", "#14b8a6"]

class ViewCPU(tk.Frame):
    def __init__(self, parent, controller=None, **kw):
        super().__init__(parent, bg=BG_MAIN, **kw)
        self.controller = controller
        
        self.process_counter = 1  
        self.anim_id = None 
        
        self._build_ui()
        self._setup_tooltip() 
        self._draw_empty_state() # Vẽ Watermark lúc mới vô

    def _build_ui(self):
        # ==========================================
        # 1. TOP FRAME (Nhập liệu & Table)
        # ==========================================
        top_frame = tk.Frame(self, bg=BG_MAIN)
        top_frame.pack(side="top", fill="x", padx=20, pady=(20, 10))

        input_card = tk.Frame(top_frame, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1, padx=20, pady=15)
        input_card.pack(side="left", fill="y", expand=False)

        tk.Label(input_card, text="Thêm Tiến Trình", font=("Segoe UI", 12, "bold"), bg=BG_CARD, fg=PRIMARY).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

        fields = [("Tên Tiến Trình:", "entry_pid", "P1"),
                  ("Thời gian đến (AT):", "entry_arrival", "0"),
                  ("Thời gian chạy (BT):", "entry_burst", "5"),
                  ("Độ ưu tiên (PR):", "entry_priority", "1")]
        
        for i, (label_text, attr_name, default_val) in enumerate(fields):
            tk.Label(input_card, text=label_text, bg=BG_CARD, font=("Segoe UI", 10)).grid(row=i+1, column=0, sticky="w", pady=5)
            entry = ttk.Entry(input_card, width=15, font=("Segoe UI", 10))
            entry.insert(0, default_val)
            entry.grid(row=i+1, column=1, sticky="e", pady=5, padx=(10, 0))
            setattr(self, attr_name, entry)

        btn_frame = tk.Frame(input_card, bg=BG_CARD)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=(15, 0))
        
        tk.Button(btn_frame, text="➕ Thêm", bg="#10b981", fg="white", font=("Segoe UI", 9, "bold"), 
                  relief="flat", cursor="hand2", width=10, command=self.add_process).pack(side="left", padx=5)
        tk.Button(btn_frame, text="❌ Xóa", bg="#ef4444", fg="white", font=("Segoe UI", 9, "bold"), 
                  relief="flat", cursor="hand2", width=10, command=self.delete_process).pack(side="left", padx=5)

        table_card = tk.Frame(top_frame, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1, padx=2, pady=2)
        table_card.pack(side="left", fill="both", expand=True, padx=(20, 0))

        # --- ZEBRA STRIPES CHO TABLE ---
        style = ttk.Style()
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#f1f5f9", foreground=TEXT_MAIN)
        
        columns = ("pid", "arrival", "burst", "priority")
        self.tree = ttk.Treeview(table_card, columns=columns, show="headings", height=7)
        
        self.tree.heading("pid", text="PID")
        self.tree.heading("arrival", text="T.Gian Đến")
        self.tree.heading("burst", text="T.Gian Chạy")
        self.tree.heading("priority", text="Ưu Tiên")

        for col in columns:
            self.tree.column(col, anchor="center", width=80)

        # Cấu hình 2 tag màu xen kẽ
        self.tree.tag_configure("evenrow", background="#f8fafc")
        self.tree.tag_configure("oddrow", background="#ffffff")

        scroll_y = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        # ==========================================
        # 2. MIDDLE FRAME (Thuật toán)
        # ==========================================
        control_card = tk.Frame(self, bg="#f1f5f9", highlightbackground=BORDER, highlightthickness=1, padx=20, pady=12)
        control_card.pack(side="top", fill="x", padx=20, pady=5)

        tk.Label(control_card, text="Thuật toán:", bg="#f1f5f9", font=("Segoe UI", 10, "bold"), fg=TEXT_MAIN).pack(side="left")
        
        self.cbb_algo = ttk.Combobox(control_card, values=[
            "FCFS (First Come First Serve)", 
            "SJF (Non Preemptive)", 
            "SRTF (Preemptive)", 
            "Priority", 
            "Round Robin"
        ], state="readonly", width=25, font=("Segoe UI", 10))
        self.cbb_algo.current(0)
        self.cbb_algo.pack(side="left", padx=(10, 20))
        self.cbb_algo.bind("<<ComboboxSelected>>", self._on_algo_change)

        self.lbl_quantum = tk.Label(control_card, text="Quantum (q):", bg="#f1f5f9", font=("Segoe UI", 10), state="disabled")
        self.lbl_quantum.pack(side="left")
        
        self.entry_quantum = ttk.Entry(control_card, width=5, font=("Segoe UI", 10), state="disabled")
        self.entry_quantum.insert(0, "2")
        self.entry_quantum.pack(side="left", padx=(5, 20))

        tk.Button(control_card, text="🚀 CHẠY MÔ PHỎNG", bg=PRIMARY, fg="white", font=("Segoe UI", 10, "bold"), 
                  relief="flat", cursor="hand2", padx=20, command=self.start_simulation).pack(side="right")
        
        tk.Button(control_card, text="🔄 Reset Data", bg="#ffffff", fg=TEXT_MAIN, font=("Segoe UI", 10, "bold"), 
                  relief="flat", cursor="hand2", highlightbackground=BORDER, highlightthickness=1, 
                  command=self.clear_all).pack(side="right", padx=10)

        # ==========================================
        # 3. BOTTOM FRAME (Gantt Chart)
        # ==========================================
        gantt_card = tk.Frame(self, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1, padx=20, pady=15)
        gantt_card.pack(side="top", fill="both", expand=True, padx=20, pady=(5, 20))

        header_gantt = tk.Frame(gantt_card, bg=BG_CARD)
        header_gantt.pack(fill="x", pady=(0, 10))
        tk.Label(header_gantt, text="Biểu đồ Gantt", font=("Segoe UI", 12, "bold"), bg=BG_CARD, fg=TEXT_MAIN).pack(side="left")
        
        self.lbl_stats = tk.Label(header_gantt, text="AWT: 0.00ms  |  ATAT: 0.00ms", font=("Segoe UI", 11, "bold"), bg=BG_CARD, fg="#ef4444")
        self.lbl_stats.pack(side="right")

        self.canvas = tk.Canvas(gantt_card, bg=BG_MAIN, highlightthickness=1, highlightbackground=BORDER)
        self.canvas.pack(fill="both", expand=True)

    # ─────────────────────────────────────────────
    #  TOOLTIP & GIAO DIỆN PHỤ
    # ─────────────────────────────────────────────
    def _draw_empty_state(self):
        self.canvas.update()
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w > 10: 
            self.canvas.create_text(w/2, h/2, text="🚀 Nhập tiến trình và nhấn CHẠY MÔ PHỎNG", 
                                    font=("Segoe UI", 14, "italic"), fill="#94a3b8")

    def _setup_tooltip(self):
        self.tooltip_bg = self.canvas.create_rectangle(0, 0, 0, 0, fill="#1e293b", outline="#cbd5e1", width=1, state="hidden")
        self.tooltip_txt = self.canvas.create_text(0, 0, text="", fill="white", font=("Segoe UI", 9, "bold"), justify="center", state="hidden")

    def show_tooltip(self, event, text_info):
        x, y = event.x, event.y - 25
        self.canvas.itemconfig(self.tooltip_txt, text=text_info, state="normal")
        bbox = self.canvas.bbox(self.tooltip_txt)
        if bbox:
            self.canvas.coords(self.tooltip_bg, bbox[0]-10, bbox[1]-6, bbox[2]+10, bbox[3]+6)
            self.canvas.itemconfig(self.tooltip_bg, state="normal")
            self.canvas.tag_raise(self.tooltip_bg)
            self.canvas.tag_raise(self.tooltip_txt)
        self.canvas.coords(self.tooltip_txt, x, y)

    def hide_tooltip(self, event):
        self.canvas.itemconfig(self.tooltip_txt, state="hidden")
        self.canvas.itemconfig(self.tooltip_bg, state="hidden")

    # ─────────────────────────────────────────────
    #  XỬ LÝ LOGIC UI
    # ─────────────────────────────────────────────
    def _on_algo_change(self, event):
        algo = self.cbb_algo.get()
        state = "normal" if "Round Robin" in algo else "disabled"
        self.lbl_quantum.config(state=state)
        self.entry_quantum.config(state=state)

    def add_process(self):
        pid, arr, bt, pr = self.entry_pid.get().strip(), self.entry_arrival.get().strip(), self.entry_burst.get().strip(), self.entry_priority.get().strip()
        if not (pid and arr and bt and pr): return messagebox.showwarning("Thiếu", "Nhập đủ thông tin tiến trình!")
        try:
            float(arr); float(bt); int(pr)
            tag = "evenrow" if self.process_counter % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(pid, arr, bt, pr), tags=(tag,))
            
            self.process_counter += 1
            self.entry_pid.delete(0, tk.END); self.entry_pid.insert(0, f"P{self.process_counter}")
            self.entry_arrival.delete(0, tk.END); self.entry_arrival.insert(0, str(int(arr) + 1)) 
        except ValueError:
            messagebox.showerror("Lỗi", "Định dạng số không hợp lệ!")

    def delete_process(self):
        for item in self.tree.selection(): self.tree.delete(item)

    def clear_all(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        self.process_counter = 1
        self.entry_pid.delete(0, tk.END); self.entry_pid.insert(0, "P1")
        if self.anim_id: self.after_cancel(self.anim_id)
        self.canvas.delete("all")
        self._draw_empty_state()
        self.lbl_stats.config(text="AWT: 0.00ms  |  ATAT: 0.00ms")

    def start_simulation(self):
        processes = [{"pid": v[0], "arrival": float(v[1]), "burst": float(v[2]), "priority": int(v[3])} 
                     for v in [self.tree.item(i, "values") for i in self.tree.get_children()]]
        if not processes: return messagebox.showwarning("Cảnh báo", "Bảng dữ liệu trống!")

        algo = self.cbb_algo.get()
        quantum = float(self.entry_quantum.get()) if "Round Robin" in algo else 0

        if self.controller: self.controller.run_cpu_scheduling(processes, algo, quantum)
        else: self._demo_gantt(processes)

    # ─────────────────────────────────────────────
    #  VẼ GANTT CHART (ĐÃ ĐƯỢC TỐI ƯU HIỆU NĂNG)
    # ─────────────────────────────────────────────
    def update_result(self, gantt_data, awt, atat):
        self.lbl_stats.config(text=f"AWT: {awt:.2f}ms  |  ATAT: {atat:.2f}ms")
        self.draw_gantt_chart_animated(gantt_data)

    def draw_gantt_chart_animated(self, gantt_data):
        if self.anim_id: self.after_cancel(self.anim_id) 
        self.canvas.delete("all")
        if not gantt_data: return

        self.canvas.update()
        C_WIDTH, C_HEIGHT = self.canvas.winfo_width() - 60, self.canvas.winfo_height()
        total_time = max(item["end"] for item in gantt_data)
        if total_time == 0: return
        
        scale = C_WIDTH / total_time
        pids = list(set(item["pid"] for item in gantt_data if item["pid"] != "IDLE"))
        color_map = {pid: GANTT_COLORS[i % len(GANTT_COLORS)] for i, pid in enumerate(pids)}

        y1, y2 = C_HEIGHT // 2 - 35, C_HEIGHT // 2 + 25
        offset_x = 30

        # Mốc 0
        self.canvas.create_line(offset_x, y2, offset_x, y2 + 10, fill="#334155", width=2)
        self.canvas.create_text(offset_x, y2 + 20, text="0", font=("Segoe UI", 9, "bold"))

        def draw_step(index):
            if index >= len(gantt_data): return 

            item = gantt_data[index]
            x1, x2 = offset_x + item["start"] * scale, offset_x + item["end"] * scale
            
            if item["pid"] == "IDLE":
                self.canvas.create_rectangle(x1, y1, x2, y2, fill="#f1f5f9", outline="#94a3b8", dash=(4, 4))
            else:
                # BỎ DROP SHADOW Ở ĐÂY ĐỂ GIẢM LOAD CHO CANVAS
                color = color_map[item["pid"]]
                rect = self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="white", width=2)
                
                if (x2 - x1) > 25: 
                    self.canvas.create_text((x1 + x2)/2, (y1 + y2)/2, text=item["pid"], font=("Segoe UI", 11, "bold"), fill="white")
                
                info = f"{item['pid']}\nStart: {item['start']:g}s | End: {item['end']:g}s\nRun: {item['end']-item['start']:g}s"
                self.canvas.tag_bind(rect, "<Enter>", lambda e, txt=info: self.show_tooltip(e, txt))
                self.canvas.tag_bind(rect, "<Leave>", self.hide_tooltip)
                self.canvas.tag_bind(rect, "<Motion>", lambda e, txt=info: self.show_tooltip(e, txt))

            # LƯỚI NỀN GRID mờ
            self.canvas.create_line(x2, y1 - 15, x2, y2 + 5, fill="#cbd5e1", dash=(2, 4))
            
            # Vạch thời gian
            self.canvas.create_line(x2, y2, x2, y2 + 10, fill="#334155", width=2)
            self.canvas.create_text(x2, y2 + 20, text=f"{item['end']:g}", font=("Segoe UI", 9, "bold"))

            # TĂNG DELAY ANIMATION LÊN 700ms GIÚP APP MƯỢT HƠN
            self.anim_id = self.after(700, lambda: draw_step(index + 1))

        draw_step(0)

    def _demo_gantt(self, processes):
        gantt_data = []
        current_time = 0
        for p in processes:
            start = max(current_time, p["arrival"])
            end = start + p["burst"]
            if start > current_time: gantt_data.append({"pid": "IDLE", "start": current_time, "end": start})
            gantt_data.append({"pid": p["pid"], "start": start, "end": end})
            current_time = end
        self.update_result(gantt_data, awt=10.5, atat=15.2)