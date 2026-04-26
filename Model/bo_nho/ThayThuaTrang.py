

from dataclasses import dataclass, field
from collections import deque

@dataclass
class BuocThayTrang:
    """Trạng thái sau một lần truy cập trang."""
    buoc:        int          
    trang:       int          
    frames:      list[int | None]  
    page_fault:  bool         
    trang_bi_thay: int | None  

    def to_dict(self) -> dict:
        return {
            "buoc":          self.buoc,
            "trang":         self.trang,
            "frames":        self.frames,
            "page_fault":    self.page_fault,
            "trang_bi_thay": self.trang_bi_thay,
        }


@dataclass
class KetQuaThayTrang:
    """Kết quả hoàn chỉnh sau khi chạy một thuật toán thay thế trang."""

    thuat_toan:  str
    so_frame:    int
    chuoi_trang: list[int]
    buoc:        list[BuocThayTrang]

    @property
    def so_page_fault(self) -> int:
        return sum(1 for b in self.buoc if b.page_fault)

    @property
    def ty_le_page_fault(self) -> float:
        if not self.buoc:
            return 0.0
        return round(self.so_page_fault / len(self.buoc) * 100, 2)

    @property
    def so_page_hit(self) -> int:
        return len(self.buoc) - self.so_page_fault

    def to_dict(self) -> dict:
        return {
            "thuat_toan":       self.thuat_toan,
            "so_frame":         self.so_frame,
            "chuoi_trang":      self.chuoi_trang,
            "so_page_fault":    self.so_page_fault,
            "so_page_hit":      self.so_page_hit,
            "ty_le_page_fault": self.ty_le_page_fault,
            "buoc":             [b.to_dict() for b in self.buoc],
        }

def fifo(chuoi_trang: list[int], so_frame: int) -> KetQuaThayTrang:
    """
    FIFO Page Replacement.
    Thay trang đã ở trong bộ nhớ lâu nhất (vào trước ra trước).
    """
    _kiem_tra_dau_vao(chuoi_trang, so_frame)

    frames        = [None] * so_frame   
    hang_doi      = deque()             
    buoc_list     = []

    for i, trang in enumerate(chuoi_trang):
        trang_bi_thay = None

        if trang in frames:
            page_fault = False
        else:
            page_fault = True

            if None in frames:
                vi_tri = frames.index(None)
                frames[vi_tri] = trang
                hang_doi.append(trang)
            else:
                trang_bi_thay = hang_doi.popleft()
                vi_tri = frames.index(trang_bi_thay)
                frames[vi_tri] = trang
                hang_doi.append(trang)

        buoc_list.append(BuocThayTrang(
            buoc=i,
            trang=trang,
            frames=frames.copy(),
            page_fault=page_fault,
            trang_bi_thay=trang_bi_thay,
        ))

    return KetQuaThayTrang("FIFO", so_frame, chuoi_trang, buoc_list)


def lru(chuoi_trang: list[int], so_frame: int) -> KetQuaThayTrang:
    """
    LRU Page Replacement.
    Thay trang lâu chưa được truy cập nhất.
    """
    _kiem_tra_dau_vao(chuoi_trang, so_frame)

    frames        = [None] * so_frame
    lan_dung_cuoi = {}  
    buoc_list     = []

    for i, trang in enumerate(chuoi_trang):
        trang_bi_thay = None

        if trang in frames:
            page_fault = False
        else:
            page_fault = True

            if None in frames:
                vi_tri = frames.index(None)
                frames[vi_tri] = trang
            else:
                trang_bi_thay = min(
                    (f for f in frames if f is not None),
                    key=lambda f: lan_dung_cuoi.get(f, -1)
                )
                vi_tri = frames.index(trang_bi_thay)
                frames[vi_tri] = trang

        lan_dung_cuoi[trang] = i

        buoc_list.append(BuocThayTrang(
            buoc=i,
            trang=trang,
            frames=frames.copy(),
            page_fault=page_fault,
            trang_bi_thay=trang_bi_thay,
        ))

    return KetQuaThayTrang("LRU", so_frame, chuoi_trang, buoc_list)


def optimal(chuoi_trang: list[int], so_frame: int) -> KetQuaThayTrang:
    """
    Optimal Page Replacement.
    Thay trang sẽ không được dùng trong thời gian dài nhất ở tương lai.
    """
    _kiem_tra_dau_vao(chuoi_trang, so_frame)

    frames    = [None] * so_frame
    buoc_list = []

    for i, trang in enumerate(chuoi_trang):
        trang_bi_thay = None

        if trang in frames:
            page_fault = False
        else:
            page_fault = True

            if None in frames:
                vi_tri = frames.index(None)
                frames[vi_tri] = trang
            else:
                def lan_dung_tiep_theo(f):
                    tuong_lai = chuoi_trang[i + 1:]
                    if f in tuong_lai:
                        return tuong_lai.index(f)
                    return float('inf')   

                trang_bi_thay = max(
                    (f for f in frames if f is not None),
                    key=lan_dung_tiep_theo
                )
                vi_tri = frames.index(trang_bi_thay)
                frames[vi_tri] = trang

        buoc_list.append(BuocThayTrang(
            buoc=i,
            trang=trang,
            frames=frames.copy(),
            page_fault=page_fault,
            trang_bi_thay=trang_bi_thay,
        ))

    return KetQuaThayTrang("Optimal", so_frame, chuoi_trang, buoc_list)

def so_sanh(chuoi_trang: list[int], so_frame: int) -> dict:
    """
    Chạy cả 3 thuật toán với cùng đầu vào và trả kết quả so sánh.
    Tiện dùng cho Controller khi cần hiển thị bảng so sánh.
    """
    ket_qua_fifo    = fifo(chuoi_trang, so_frame)
    ket_qua_lru     = lru(chuoi_trang, so_frame)
    ket_qua_optimal = optimal(chuoi_trang, so_frame)

    return {
        "chuoi_trang": chuoi_trang,
        "so_frame":    so_frame,
        "fifo":    {
            "so_page_fault":    ket_qua_fifo.so_page_fault,
            "ty_le_page_fault": ket_qua_fifo.ty_le_page_fault,
            "chi_tiet":         ket_qua_fifo.to_dict(),
        },
        "lru":     {
            "so_page_fault":    ket_qua_lru.so_page_fault,
            "ty_le_page_fault": ket_qua_lru.ty_le_page_fault,
            "chi_tiet":         ket_qua_lru.to_dict(),
        },
        "optimal": {
            "so_page_fault":    ket_qua_optimal.so_page_fault,
            "ty_le_page_fault": ket_qua_optimal.ty_le_page_fault,
            "chi_tiet":         ket_qua_optimal.to_dict(),
        },
    }

def _kiem_tra_dau_vao(chuoi_trang: list[int], so_frame: int):
    if not chuoi_trang:
        raise ValueError("Chuỗi trang không được rỗng")
    if so_frame <= 0:
        raise ValueError("Số frame phải > 0")
    if any(t < 0 for t in chuoi_trang):
        raise ValueError("Số trang phải >= 0")