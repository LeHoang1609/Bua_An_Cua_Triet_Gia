import tkinter as tk
from tkinter import ttk

# ==========================================
# 🎨 BẢNG MÀU MODERN UI (Giả lập Bootstrap)
# ==========================================
BG_MAIN    = "#f5f6fa"   
BG_CARD    = "#ffffff"   
PRIMARY    = "#4a69bd"   
BTN_BLUE   = "#1e90ff"   
BTN_GREEN  = "#2ed573"   
BTN_GRAY   = "#dfe4ea"   
TEXT_MAIN  = "#2f3542"   
TEXT_SUB   = "#a4b0be"
BORDER     = "#dcdde1"   

class ViewBoNho(tk.Frame):
    def __init__(self, parent, controller=None, **kw):
        super().__init__(parent, bg=BG_MAIN, **kw)
        self.controller = controller
        
        self._build_ui()
        self._render_fake_data()

    def _build_ui(self):
        # ==========================================
        # 1. INPUT PANEL (CARD 1)
        # ==========================================
        input_card = tk.Frame(self, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1)
        input_card.pack(fill="x", padx=20, pady=(20, 10))

        tk.Label(input_card, text="⚙️ CẤU HÌNH THÔNG SỐ", font=("Segoe UI", 11, "bold"), 
                 bg=BG_CARD, fg=PRIMARY).pack(anchor="w", padx=15, pady=(10, 5))

        row_input = tk.Frame(input_card, bg=BG_CARD)
        row_input.pack(fill="x", padx=15, pady=(0, 15))

        # Chuỗi tham chiếu
        tk.Label(row_input, text="Chuỗi tham chiếu:", bg=BG_CARD, font=("Segoe UI", 10), fg=TEXT_MAIN).grid(row=0, column=0, sticky="w", pady=5)
        self.ent_sequence = tk.Entry(row_input, width=40, font=("Segoe UI", 10), bg=BG_MAIN, relief="flat")
        self.ent_sequence.insert(0, "7, 0, 1, 2, 0, 3, 0, 4, 2, 3")
        self.ent_sequence.grid(row=0, column=1, padx=(10, 30))

        # Số frame
        tk.Label(row_input, text="Số khung (Frames):", bg=BG_CARD, font=("Segoe UI", 10), fg=TEXT_MAIN).grid(row=0, column=2, sticky="w")
        self.ent_frames = tk.Spinbox(row_input, from_=1, to=10, width=5, font=("Segoe UI", 10), bg=BG_MAIN, relief="flat")
        self.ent_frames.delete(0, "end")
        self.ent_frames.insert(0, "3")
        self.ent_frames.grid(row=0, column=3, padx=10)

        # Thuật toán
        tk.Label(row_input, text="Thuật toán:", bg=BG_CARD, font=("Segoe UI", 10), fg=TEXT_MAIN).grid(row=1, column=0, sticky="w", pady=5)
        self.cbb_algo = ttk.Combobox(row_input, values=["FIFO (First-In-First-Out)", "LRU (Least Recently Used)", "Optimal"], 
                                     state="readonly", width=38, font=("Segoe UI", 10))
        self.cbb_algo.current(0)
        self.cbb_algo.grid(row=1, column=1, padx=(10, 30))

        # ==========================================
        # 2. CONTROL PANEL (CARD 2)
        # ==========================================
        control_card = tk.Frame(self, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1)
        control_card.pack(fill="x", padx=20, pady=5)

        btn_frame = tk.Frame(control_card, bg=BG_CARD)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="▶ Chạy Auto", bg=BTN_BLUE, fg="white", 
                  font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=4, cursor="hand2").pack(side="left", padx=10)
        
        tk.Button(btn_frame, text="⏸ Step (Từng bước)", bg=BTN_GREEN, fg="white", 
                  font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=4, cursor="hand2").pack(side="left", padx=10)
        
        tk.Button(btn_frame, text="🔄 Reset", bg=BTN_GRAY, fg=TEXT_MAIN, 
                  font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=4, cursor="hand2").pack(side="left", padx=10)

        # ==========================================
        # 3. VISUAL PANEL (CARD 3)
        # ==========================================
        self.visual_card = tk.Frame(self, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1)
        self.visual_card.pack(fill="both", expand=True, padx=20, pady=(10, 15))

        top_visual = tk.Frame(self.visual_card, bg=BG_CARD)
        top_visual.pack(fill="x", padx=15, pady=10)

        tk.Label(top_visual, text="📊 BẢNG MÔ PHỎNG", font=("Segoe UI", 11, "bold"), bg=BG_CARD, fg=PRIMARY).pack(side="left")
        self.lbl_faults = tk.Label(top_visual, text="Page Faults: 0", font=("Segoe UI", 12, "bold"), bg=BG_CARD, fg="#ff4757")
        self.lbl_faults.pack(side="right")

        # ==========================================
        # SCROLL CONTAINER — ngang + dọc
        # ==========================================
        table_container = tk.Frame(self.visual_card, bg=BG_CARD)
        table_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Cấu hình grid để Canvas chiếm hết không gian
        table_container.rowconfigure(0, weight=1)
        table_container.columnconfigure(0, weight=1)

        # Canvas chứa bảng
        self.canvas_scroll = tk.Canvas(table_container, bg=BG_CARD, highlightthickness=0)
        self.canvas_scroll.grid(row=0, column=0, sticky="nsew")

        # ── Thanh cuộn dọc (mới thêm) ──────────────────────────────────
        vbar = ttk.Scrollbar(table_container, orient="vertical", command=self.canvas_scroll.yview)
        vbar.grid(row=0, column=1, sticky="ns")

        # ── Thanh cuộn ngang ────────────────────────────────────────────
        hbar = ttk.Scrollbar(table_container, orient="horizontal", command=self.canvas_scroll.xview)
        hbar.grid(row=1, column=0, sticky="ew")

        # Kết nối cả hai thanh cuộn vào Canvas
        self.canvas_scroll.config(
            xscrollcommand=hbar.set,
            yscrollcommand=vbar.set
        )

        # Frame thực sự chứa Grid bảng
        self.table_frame = tk.Frame(self.canvas_scroll, bg=BG_CARD)
        self.canvas_window = self.canvas_scroll.create_window((0, 0), window=self.table_frame, anchor="nw")

        # Cập nhật scrollregion khi nội dung thay đổi
        self.table_frame.bind(
            "<Configure>",
            lambda e: self.canvas_scroll.config(scrollregion=self.canvas_scroll.bbox("all"))
        )

        # Hỗ trợ cuộn bằng chuột (scroll dọc)
        self.canvas_scroll.bind("<Enter>", self._bind_mousewheel)
        self.canvas_scroll.bind("<Leave>", self._unbind_mousewheel)

    # ── Cuộn chuột ──────────────────────────────────────────────────────

    def _bind_mousewheel(self, event):
        self.canvas_scroll.bind_all("<MouseWheel>", self._on_mousewheel)          # Windows
        self.canvas_scroll.bind_all("<Button-4>",   self._on_mousewheel_linux)    # Linux scroll up
        self.canvas_scroll.bind_all("<Button-5>",   self._on_mousewheel_linux)    # Linux scroll down

    def _unbind_mousewheel(self, event):
        self.canvas_scroll.unbind_all("<MouseWheel>")
        self.canvas_scroll.unbind_all("<Button-4>")
        self.canvas_scroll.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        self.canvas_scroll.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_linux(self, event):
        if event.num == 4:
            self.canvas_scroll.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas_scroll.yview_scroll(1, "units")

    # ==========================================
    # 🧠 FAKE DATA ĐỂ RENDER TRƯỚC UI
    # ==========================================
    def _render_fake_data(self):
        self.status = tk.Label(self, text=" Sẵn sàng chờ cấu hình...", anchor="w", 
                               bg=BTN_GRAY, fg=TEXT_MAIN, font=("Segoe UI", 9), pady=4)
        self.status.pack(fill="x", side="bottom")

        seq = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3]
        matrix = [
            [7, 7, 7, 2, 2, 2, 2, 4, 4, 4],
            ["", 0, 0, 0, 0, 3, 3, 3, 2, 2],
            ["", "", 1, 1, 1, 1, 0, 0, 0, 3],
            ["", "", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", "", ""],
        ]
        faults = ["F", "F", "F", "F", "H", "F", "F", "F", "F", "F"]

        for widget in self.table_frame.winfo_children():
            widget.destroy()

        # Hàng tiêu đề
        tk.Label(self.table_frame, text="Reference", width=12, bg=BG_MAIN, 
                 font=("Segoe UI", 9, "bold"), fg=TEXT_MAIN).grid(row=0, column=0, padx=5, pady=2, sticky="nsew")
        
        for j, val in enumerate(seq):
            lbl = tk.Label(self.table_frame, text=str(val), width=4, height=2, bg=BG_MAIN, 
                           font=("Segoe UI", 11, "bold"), fg=PRIMARY, borderwidth=1, relief="solid")
            lbl.grid(row=0, column=j+1, padx=2, pady=2, sticky="nsew")

        # Các hàng Frame
        for i, row in enumerate(matrix):
            tk.Label(self.table_frame, text=f"Frame {i}", width=12, bg=BG_CARD, 
                     font=("Segoe UI", 9, "bold"), fg=TEXT_MAIN).grid(row=i+1, column=0, padx=5, pady=2, sticky="nsew")
            
            for j, val in enumerate(row):
                txt = str(val) if val != "" else "–"
                color_fg = TEXT_MAIN if val != "" else TEXT_SUB
                lbl = tk.Label(self.table_frame, text=txt, width=4, height=2, bg="white", 
                               font=("Segoe UI", 11), fg=color_fg, borderwidth=1, relief="solid")
                lbl.grid(row=i+1, column=j+1, padx=2, pady=2, sticky="nsew")

        # Hàng trạng thái
        tk.Label(self.table_frame, text="Status", width=12, bg=BG_CARD, 
                 font=("Segoe UI", 9, "bold"), fg=TEXT_MAIN).grid(row=len(matrix)+1, column=0, padx=5, pady=(15, 2), sticky="nsew")
        
        for j, val in enumerate(faults):
            color_bg = "#ff4757" if val == "F" else "#2ed573"
            lbl = tk.Label(self.table_frame, text=val, width=4, height=1, bg=color_bg, fg="white", 
                           font=("Segoe UI", 10, "bold"), borderwidth=1, relief="solid")
            lbl.grid(row=len(matrix)+1, column=j+1, padx=2, pady=(15, 2), sticky="nsew")

        self.lbl_faults.config(text="Page Faults: 6  (60.0%)")
        self.status.config(text=" Đã tải Fake Data mẫu thành công. Bảng đã được căn giữa và thêm thanh cuộn!")