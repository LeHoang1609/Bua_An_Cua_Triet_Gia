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

    # ── Vẽ bảng grid (Đã Tối Ưu Chống Lag) ───────────────────────────────

    def _xoa_bang(self):
        """Xóa sạch bảng khi người dùng nhấn Reset"""
        for w in self.view.table_frame.winfo_children():
            w.destroy()
        self.view.cells.clear()

    def _ve_bang_rong(self, ket_qua: KetQuaThayTrang):
        """Vẽ khung bảng chỉ có header (chuỗi tham chiếu)."""
        self._ve_bang_den_buoc(ket_qua, 0)

    def _ve_bang_day_du(self, ket_qua: KetQuaThayTrang):
        """Vẽ toàn bộ bảng (tất cả bước)."""
        self._ve_bang_den_buoc(ket_qua, len(ket_qua.buoc))

    def _ve_bang_den_buoc(self, ket_qua: KetQuaThayTrang, den_buoc: int):
        """
        Cập nhật dữ liệu vào lưới có sẵn (chống lag).
        Không dùng destroy() để tránh rò rỉ bộ nhớ.
        """
        n_frame = ket_qua.so_frame
        n_col = len(ket_qua.chuoi_trang)
        
        # Chỉ khởi tạo lại lưới Label nếu lưới hiện tại không khớp kích thước
        # (VD: Người dùng đổi số Frame hoặc thêm bớt chuỗi tham chiếu)
        if not self.view.cells or f"{n_frame-1}_{n_col-1}" not in self.view.cells:
            self.view.prepare_grid(n_frame, n_col)

        # 1. Cập nhật Header
        for j, trang in enumerate(ket_qua.chuoi_trang):
            bg = "#dbeafe" if j == den_buoc - 1 else "#f8fafc"
            self.view.cells[f"h_{j}"].config(text=str(trang), bg=bg)

        # 2. Cập nhật Frames
        for fi in range(n_frame):
            for j in range(n_col):
                val = "–"
                bg_cell = COLOR_NORMAL
                fg_cell = "#94a3b8"

                if j < den_buoc:
                    buoc = ket_qua.buoc[j]
                    v = buoc.frames[fi]
                    if v is not None:
                        val = str(v)
                        fg_cell = "#1e293b"
                    
                    # Tô vàng ô vừa bị thay
                    if buoc.page_fault and buoc.trang_bi_thay == v:
                        bg_cell = COLOR_REPLACED

                self.view.cells[f"{fi}_{j}"].config(text=val, bg=bg_cell, fg=fg_cell)

        # 3. Cập nhật Status Hit/Fault
        for j in range(n_col):
            txt = ""
            bg_sts = "#f1f5f9"
            fg_sts = "#1e293b"

            if j < den_buoc:
                txt = "F" if ket_qua.buoc[j].page_fault else "H"
                bg_sts = COLOR_FAULT if txt == "F" else COLOR_HIT
                fg_sts = "white"

            self.view.cells[f"s_{j}"].config(text=txt, bg=bg_sts, fg=fg_sts)