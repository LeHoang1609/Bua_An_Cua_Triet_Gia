

import logging
from Model.bo_nho.ThayThuaTrang import fifo, lru, optimal, KetQuaThayTrang, BuocThayTrang

logger = logging.getLogger(__name__)

# ── Màu sắc ô grid (Controller quy định, View dùng) ─────────────────────
COLOR_FAULT    = "#ff4757"   # đỏ  — page fault
COLOR_HIT      = "#2ed573"   # xanh — page hit
COLOR_NORMAL   = "#ffffff"   # trắng — ô bình thường
COLOR_REPLACED = "#ffeaa7"   # vàng nhạt — ô vừa bị thay

ALGO_MAP = {
    "FIFO (First-In-First-Out)":  "fifo",
    "LRU (Least Recently Used)":  "lru",
    "Optimal":                    "optimal",
}


class ControllerBoNho:
    

    def __init__(self, view):
        self.view            = view
        self._ket_qua: KetQuaThayTrang | None = None
        self._step_index     = 0
        self._step_job       = None   # after() job ID cho auto mode

        # Bind các nút trong View vào Controller
        self._bind_buttons()

    # ── Bind nút vào View ────────────────────────────────────────────────

    def _bind_buttons(self):
        """
        ViewBoNho chưa gắn command cho các nút.
        Controller tìm và bind vào đây.
        """
        try:
            btn_frame = None
            # Tìm frame chứa các nút trong visual_card
            for widget in self.view.winfo_children():
                for child in widget.winfo_children():
                    if hasattr(child, 'winfo_children'):
                        children = child.winfo_children()
                        # Frame chứa 3 Button liên tiếp
                        btns = [w for w in children if isinstance(w, __import__('tkinter').Button)]
                        if len(btns) >= 3:
                            btn_frame = children
                            break

            # Bind theo text nút
            import tkinter as tk
            def _find_buttons(widget):
                result = []
                for child in widget.winfo_children():
                    if isinstance(child, tk.Button):
                        result.append(child)
                    result.extend(_find_buttons(child))
                return result

            all_btns = _find_buttons(self.view)
            for btn in all_btns:
                txt = btn.cget("text")
                if "Auto" in txt:
                    btn.config(command=self.chay_auto)
                elif "Step" in txt or "Từng" in txt:
                    btn.config(command=self.chay_step)
                elif "Reset" in txt:
                    btn.config(command=self.reset)
        except Exception as e:
            logger.warning(f"Không bind được nút ViewBoNho: {e}")

    # ── Lệnh từ View ─────────────────────────────────────────────────────

    def chay_auto(self):
        """Chạy toàn bộ thuật toán và hiển thị kết quả ngay."""
        ket_qua = self._lay_va_tinh()
        if not ket_qua:
            return
        self._ket_qua    = ket_qua
        self._step_index = len(ket_qua.buoc)   # đánh dấu đã xem hết
        self._ve_bang_day_du(ket_qua)
        self._cap_nhat_fault(ket_qua.so_page_fault, ket_qua.ty_le_page_fault)

    def chay_step(self):
        """Hiển thị từng bước một khi người dùng nhấn."""
        if not self._ket_qua:
            self._ket_qua    = self._lay_va_tinh()
            self._step_index = 0
            if not self._ket_qua:
                return
            # Vẽ khung rỗng trước
            self._ve_bang_rong(self._ket_qua)

        if self._step_index < len(self._ket_qua.buoc):
            self._step_index += 1
            self._ve_bang_den_buoc(self._ket_qua, self._step_index)
            fault_den_gio = sum(
                1 for b in self._ket_qua.buoc[:self._step_index]
                if b.page_fault
            )
            self.view.lbl_faults.config(
                text=f"Page Faults: {fault_den_gio} / {self._step_index} bước"
            )

    def reset(self):
        """Reset về trạng thái ban đầu."""
        if self._step_job:
            self.view.after_cancel(self._step_job)
            self._step_job = None
        self._ket_qua    = None
        self._step_index = 0
        self.view.lbl_faults.config(text="Page Faults: 0")
        self._xoa_bang()
        try:
            self.view.status.config(text=" Đã reset. Sẵn sàng chạy lại.")
        except Exception:
            pass

    # ── Xử lý nội bộ ─────────────────────────────────────────────────────

    def _lay_va_tinh(self) -> KetQuaThayTrang | None:
        """Đọc input từ View, validate và chạy thuật toán."""
        try:
            # Đọc chuỗi tham chiếu
            raw = self.view.ent_sequence.get().strip()
            chuoi = [int(x.strip()) for x in raw.replace(",", " ").split() if x.strip()]
            if not chuoi:
                raise ValueError("Chuỗi trang rỗng")

            # Đọc số frame
            so_frame = int(self.view.ent_frames.get())
            if so_frame <= 0:
                raise ValueError("Số frame phải > 0")

            # Đọc thuật toán
            algo_name = self.view.cbb_algo.get()
            ten_algo  = ALGO_MAP.get(algo_name, "fifo")

        except ValueError as e:
            logger.warning(f"Input không hợp lệ: {e}")
            try:
                self.view.status.config(text=f" ⚠ Lỗi nhập liệu: {e}")
            except Exception:
                pass
            return None

        # Chạy thuật toán
        try:
            if ten_algo == "fifo":
                return fifo(chuoi, so_frame)
            elif ten_algo == "lru":
                return lru(chuoi, so_frame)
            elif ten_algo == "optimal":
                return optimal(chuoi, so_frame)
        except Exception as e:
            logger.error(f"Lỗi thuật toán: {e}")
            return None

    def _cap_nhat_fault(self, so_fault: int, ty_le: float):
        self.view.lbl_faults.config(
            text=f"Page Faults: {so_fault}  ({ty_le}%)"
        )

    # ── Vẽ bảng grid ─────────────────────────────────────────────────────

    def _xoa_bang(self):
        for w in self.view.table_frame.winfo_children():
            w.destroy()

    def _ve_bang_rong(self, ket_qua: KetQuaThayTrang):
        """Vẽ khung bảng chỉ có header (chuỗi tham chiếu)."""
        self._ve_bang_den_buoc(ket_qua, 0)

    def _ve_bang_day_du(self, ket_qua: KetQuaThayTrang):
        """Vẽ toàn bộ bảng (tất cả bước)."""
        self._ve_bang_den_buoc(ket_qua, len(ket_qua.buoc))

    def _ve_bang_den_buoc(self, ket_qua: KetQuaThayTrang, den_buoc: int):
        """
        Vẽ lại bảng grid đến bước thứ `den_buoc`.
        Cấu trúc bảng:
            Hàng 0 : "Reference"  | trang[0] | trang[1] | ...
            Hàng 1 : "Frame 0"    | ô[0][0]  | ô[0][1]  | ...
            Hàng 2 : "Frame 1"    | ...
            ...
            Hàng N : "Status"     | F/H      | F/H      | ...
        """
        import tkinter as tk

        self._xoa_bang()

        tf    = self.view.table_frame
        chuoi = ket_qua.chuoi_trang
        buocs = ket_qua.buoc[:den_buoc]
        n_col = len(chuoi)
        n_frame = ket_qua.so_frame

        CELL_W = 4
        CELL_H = 2
        HDR_W  = 12

        # ── Hàng tiêu đề: chuỗi tham chiếu ──────────────────────────────
        tk.Label(tf, text="Reference", width=HDR_W,
                 bg="#f1f5f9", font=("Segoe UI", 9, "bold"),
                 fg="#2f3542").grid(row=0, column=0, padx=3, pady=3, sticky="nsew")

        for j, trang in enumerate(chuoi):
            # Tô màu cột đang là bước hiện tại
            bg = "#dbeafe" if j == den_buoc - 1 else "#f8fafc"
            tk.Label(tf, text=str(trang), width=CELL_W, height=CELL_H,
                     bg=bg, font=("Segoe UI", 11, "bold"),
                     fg="#2563eb", borderwidth=1, relief="solid"
                     ).grid(row=0, column=j + 1, padx=2, pady=2, sticky="nsew")

        # ── Hàng frame ────────────────────────────────────────────────────
        for fi in range(n_frame):
            tk.Label(tf, text=f"Frame {fi}", width=HDR_W,
                     bg="#ffffff", font=("Segoe UI", 9, "bold"),
                     fg="#2f3542").grid(row=fi + 1, column=0, padx=3, pady=2, sticky="nsew")

            for j in range(n_col):
                if j < len(buocs):
                    buoc  = buocs[j]
                    val   = buoc.frames[fi]
                    txt   = str(val) if val is not None else "–"
                    # Tô vàng ô vừa bị thay
                    if buoc.page_fault and buoc.trang_bi_thay == val:
                        bg_cell = COLOR_REPLACED
                    else:
                        bg_cell = COLOR_NORMAL
                    fg_cell = "#1e293b" if val is not None else "#94a3b8"
                else:
                    txt     = "–"
                    bg_cell = COLOR_NORMAL
                    fg_cell = "#94a3b8"

                tk.Label(tf, text=txt, width=CELL_W, height=CELL_H,
                         bg=bg_cell, font=("Segoe UI", 11),
                         fg=fg_cell, borderwidth=1, relief="solid"
                         ).grid(row=fi + 1, column=j + 1, padx=2, pady=2, sticky="nsew")

        # ── Hàng trạng thái Hit / Fault ───────────────────────────────────
        row_status = n_frame + 1
        tk.Label(tf, text="Status", width=HDR_W,
                 bg="#ffffff", font=("Segoe UI", 9, "bold"),
                 fg="#2f3542").grid(row=row_status, column=0, padx=3, pady=(12, 2), sticky="nsew")

        for j in range(n_col):
            if j < len(buocs):
                val    = "F" if buocs[j].page_fault else "H"
                bg_sts = COLOR_FAULT if val == "F" else COLOR_HIT
            else:
                val    = ""
                bg_sts = "#f1f5f9"

            tk.Label(tf, text=val, width=CELL_W, height=1,
                     bg=bg_sts, fg="white",
                     font=("Segoe UI", 10, "bold"),
                     borderwidth=1, relief="solid"
                     ).grid(row=row_status, column=j + 1, padx=2, pady=(12, 2), sticky="nsew")

        # Cập nhật scrollregion
        tf.update_idletasks()
        self.view.canvas_scroll.config(
            scrollregion=self.view.canvas_scroll.bbox("all")
        )