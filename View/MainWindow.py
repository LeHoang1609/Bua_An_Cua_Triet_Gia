import tkinter as tk
from tkinter import ttk
import platform

# ─────────────────────────────────────────────
#  IMPORT VIEW THẬT (Xử lý linh hoạt đường dẫn)
# ─────────────────────────────────────────────
try:
    from View.ViewTrietGia import ViewTrietGia
except ModuleNotFoundError:
    from ViewTrietGia import ViewTrietGia

# ─────────────────────────────────────────────
#  1. DPI AWARENESS (CHỐNG MỜ CHỮ TRÊN WINDOWS)
# ─────────────────────────────────────────────
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# ─────────────────────────────────────────────
#  2. PALETTE & CONSTANTS (CHUẨN ACADEMIC UI)
# ─────────────────────────────────────────────
BG_MAIN    = "#f8fafc"      
BG_SIDEBAR = "#e2e8f0"      
BG_CARD    = "#ffffff"      
TEXT_MAIN  = "#1e293b"      
TEXT_SUB   = "#64748b"      
PRIMARY    = "#2563eb"      
HOVER      = "#1d4ed8"      
BORDER     = "#e5e7eb"      

ACTIVE_BG  = "#dbeafe"      
ACTIVE_FG  = "#2563eb"      

FONT_APP   = ("Segoe UI", 18, "bold")
FONT_TITLE = ("Segoe UI", 16, "bold")
FONT_NORMAL= ("Segoe UI", 11)
FONT_SMALL = ("Segoe UI", 10)

TABS = [
    ("🍽️  Dining Philosophers", "ViewTrietGia"),
    ("⏱️  Điều phối CPU",        "ViewCPU"),
    ("🧠  Quản lý Bộ nhớ",        "ViewBoNho"),
    ("🖥️  Quản lý Tác vụ",        "ViewTaskMgr"),
]

# ─────────────────────────────────────────────
#  3. STYLE HELPERS (TTK STYLING)
# ─────────────────────────────────────────────
def apply_global_style(root: tk.Tk):
    style = ttk.Style(root)
    style.theme_use("clam")
    
    style.configure("Primary.TButton",
        background=PRIMARY, foreground="white",
        font=FONT_NORMAL, padding=(20, 8), borderwidth=0
    )
    style.map("Primary.TButton",
        background=[("active", HOVER), ("pressed", "#1e40af")],
    )

# ─────────────────────────────────────────────
#  4. SIDEBAR NAV BUTTON
# ─────────────────────────────────────────────
class NavButton(tk.Frame):
    def __init__(self, parent, label, on_click, **kw):
        super().__init__(parent, bg=BG_SIDEBAR, **kw)
        self.on_click = on_click
        self.active   = False

        self.btn_area = tk.Frame(self, bg=BG_SIDEBAR, cursor="hand2")
        self.btn_area.pack(fill="both", expand=True, padx=12, pady=2)

        self._lbl = tk.Label(self.btn_area, text=label, font=FONT_NORMAL,
                             bg=BG_SIDEBAR, fg=TEXT_MAIN,
                             anchor="w", padx=16, pady=12)
        self._lbl.pack(side="left", fill="both", expand=True)

        for w in (self.btn_area, self._lbl):
            w.bind("<Button-1>", self._clicked)
            w.bind("<Enter>",    self._hover_on)
            w.bind("<Leave>",    self._hover_off)

    def _clicked(self, _=None): self.on_click()

    def _hover_on(self, _=None):
        if not self.active:
            self.btn_area.config(bg="#cbd5e1")
            self._lbl.config(bg="#cbd5e1")

    def _hover_off(self, _=None):
        if not self.active:
            self.btn_area.config(bg=BG_SIDEBAR)
            self._lbl.config(bg=BG_SIDEBAR)

    def set_active(self, state: bool):
        self.active = state
        if state:
            self.btn_area.config(bg=ACTIVE_BG)
            self._lbl.config(bg=ACTIVE_BG, fg=ACTIVE_FG, font=("Segoe UI", 11, "bold"))
        else:
            self.btn_area.config(bg=BG_SIDEBAR)
            self._lbl.config(bg=BG_SIDEBAR, fg=TEXT_MAIN, font=FONT_NORMAL)

# ─────────────────────────────────────────────
#  5. CARD PLACEHOLDER (CHỈ DÙNG CHO CÁC TAB CHƯA LÀM)
# ─────────────────────────────────────────────
class PlaceholderFrame(tk.Frame):
    def __init__(self, parent, title, desc, **kw):
        super().__init__(parent, bg=BG_MAIN, **kw)

        card_border = tk.Frame(self, bg=BORDER)
        card_border.pack(fill="both", expand=True, padx=24, pady=24)

        card = tk.Frame(card_border, bg=BG_CARD)
        card.pack(fill="both", expand=True, padx=1, pady=1)

        header = tk.Frame(card, bg=BG_CARD)
        header.pack(fill="x", padx=32, pady=(24, 16))
        tk.Label(header, text=title, font=FONT_TITLE, bg=BG_CARD, fg=TEXT_MAIN).pack(side="left")

        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=32)

        center = tk.Frame(card, bg=BG_CARD)
        center.pack(expand=True)

        tk.Label(center, text="📦", font=("Segoe UI", 48), bg=BG_CARD, fg=PRIMARY).pack(pady=(0, 16))
        
        tk.Label(center, text=title, font=("Segoe UI", 16, "bold"),
                 bg=BG_CARD, fg=TEXT_MAIN).pack(pady=(0, 8))
                 
        tk.Label(center, text=desc, font=FONT_NORMAL, bg=BG_CARD, fg=TEXT_SUB,
                 wraplength=450, justify="center").pack(pady=(0, 24))

        btn = ttk.Button(center, text="Cấu hình mô phỏng", style="Primary.TButton", cursor="hand2")
        btn.pack()

# ─────────────────────────────────────────────
#  6. MAIN WINDOW & BỐ CỤC (LAYOUT)
# ─────────────────────────────────────────────
class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("OS Simulator – Nhóm 2")
        self.root.geometry("1100x680")
        self.root.minsize(900, 580)
        self.root.configure(bg=BG_MAIN)
        self.root.resizable(True, True)

        apply_global_style(self.root)
        self._center_window()

        self._nav_buttons: dict[str, NavButton] = {}
        self._frames:      dict[str, tk.Frame]  = {}
        self._current_key: str | None           = None

        self._build_header()
        self._build_body()
        self._build_status()
        
        # Mặc định mở tab đầu tiên khi khởi động app
        self._switch(TABS[0][1])

    def _center_window(self):
        self.root.update_idletasks()
        w  = self.root.winfo_width()
        h  = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=BG_CARD, height=64)
        hdr.pack(fill="x", side="top")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="OS Simulator", font=FONT_APP, bg=BG_CARD, fg=PRIMARY,
                 padx=24).pack(side="left", fill="y")

        tk.Label(hdr, text="Đồ án Hệ điều hành — Trực quan hoá thuật toán",
                 font=FONT_NORMAL, bg=BG_CARD, fg=TEXT_SUB).pack(side="left", fill="y", pady=(4,0))

        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x")

    def _build_body(self):
        body = tk.Frame(self.root, bg=BG_MAIN)
        body.pack(fill="both", expand=True)

        # ----- SIDEBAR -----
        sidebar = tk.Frame(body, bg=BG_SIDEBAR, width=250)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="MODULES", font=("Segoe UI", 9, "bold"),
                 bg=BG_SIDEBAR, fg=TEXT_SUB, padx=24, pady=20).pack(anchor="w")

        for label, key in TABS:
            btn = NavButton(sidebar, label, on_click=lambda k=key: self._switch(k))
            btn.pack(fill="x")
            self._nav_buttons[key] = btn

        tk.Frame(body, bg=BORDER, width=1).pack(side="left", fill="y")

        # ----- CONTENT -----
        content = tk.Frame(body, bg=BG_MAIN)
        content.pack(side="left", fill="both", expand=True)

        descs = {
            "ViewTrietGia": "", # Đã có class riêng, không cần desc
            "ViewCPU":      "Nhập danh sách các tiến trình, vẽ biểu đồ Gantt. Tự động tính toán thời gian chờ & đáp ứng theo các thuật toán FCFS, SJF, Priority, RR.",
            "ViewBoNho":    "Mô phỏng quá trình dịch địa chỉ luận lý sang vật lý. Trực quan hoá thuật toán thay thế trang (Page Replacement) FIFO & LRU.",
            "ViewTaskMgr":  "Liệt kê các tiến trình đang hoạt động trong hệ thống. Theo dõi biểu đồ tài nguyên CPU/RAM và cho phép thao tác Kill process.",
        }

        # KHÚC QUAN TRỌNG: FIX LỖI Ở ĐÂY
        for label, key in TABS:
            if key == "ViewTrietGia":
                frame = ViewTrietGia(content)   # Dùng view thật
            else:
                frame = PlaceholderFrame(content, label, descs[key])

            frame.place(relwidth=1, relheight=1)
            self._frames[key] = frame

    def _build_status(self):
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x")
        
        status_bar = tk.Frame(self.root, bg=BG_SIDEBAR, height=32)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)

        self._lbl_status = tk.Label(status_bar, text="Sẵn sàng", font=FONT_SMALL,
                                    bg=BG_SIDEBAR, fg=TEXT_SUB, padx=16)
        self._lbl_status.pack(side="left", fill="y")

        py_ver  = platform.python_version()
        os_info = f"{platform.system()} {platform.release()}"

        tk.Label(status_bar, text=os_info, font=FONT_SMALL,
                 bg=BG_SIDEBAR, fg=TEXT_SUB, padx=16).pack(side="right", fill="y")
        tk.Frame(status_bar, bg=BORDER, width=1).pack(side="right", fill="y", pady=6)
        tk.Label(status_bar, text=f"Python {py_ver}", font=FONT_SMALL,
                 bg=BG_SIDEBAR, fg=TEXT_SUB, padx=16).pack(side="right", fill="y")

    # ── navigation ───────────────────────────
    def _switch(self, key: str):
        if self._current_key == key:
            return
        if self._current_key:
            self._nav_buttons[self._current_key].set_active(False)
            self._frames[self._current_key].lower()
            
        self._current_key = key
        self._nav_buttons[key].set_active(True)
        
        # Kéo frame hiển thị lên trên cùng
        self._frames[key].lift()
        
        label = next(l for l, k in TABS if k == key)
        self._lbl_status.config(text=f"Đang làm việc: {label}")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = MainWindow()
    app.run()