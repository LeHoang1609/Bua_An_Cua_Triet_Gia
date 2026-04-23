

from dataclasses import dataclass


@dataclass
class KetQuaDich:
    """Kết quả dịch địa chỉ của một lần truy cập."""

    dia_chi_luan_ly:  int       
    kich_thuoc_trang: int       
    so_trang:         int       
    offset:           int      
    so_frame:         int | None  
    dia_chi_vat_ly:   int | None  
    page_fault:       bool      

    def to_dict(self) -> dict:
        return {
            "dia_chi_luan_ly":  self.dia_chi_luan_ly,
            "kich_thuoc_trang": self.kich_thuoc_trang,
            "so_trang":         self.so_trang,
            "offset":           self.offset,
            "so_frame":         self.so_frame,
            "dia_chi_vat_ly":   self.dia_chi_vat_ly,
            "page_fault":       self.page_fault,
        }


def dich_dia_chi(
    dia_chi_luan_ly:  int,
    kich_thuoc_trang: int,
    page_table:       dict[int, int],
) -> KetQuaDich:
    if dia_chi_luan_ly < 0:
        raise ValueError("Địa chỉ luận lý phải >= 0")
    if kich_thuoc_trang <= 0 or (kich_thuoc_trang & (kich_thuoc_trang - 1)) != 0:
        raise ValueError("Kích thước trang phải là lũy thừa của 2")

    so_trang = dia_chi_luan_ly // kich_thuoc_trang
    offset   = dia_chi_luan_ly  % kich_thuoc_trang

    if so_trang not in page_table:
        return KetQuaDich(
            dia_chi_luan_ly  = dia_chi_luan_ly,
            kich_thuoc_trang = kich_thuoc_trang,
            so_trang         = so_trang,
            offset           = offset,
            so_frame         = None,
            dia_chi_vat_ly   = None,
            page_fault       = True,
        )

    so_frame       = page_table[so_trang]
    dia_chi_vat_ly = so_frame * kich_thuoc_trang + offset

    return KetQuaDich(
        dia_chi_luan_ly  = dia_chi_luan_ly,
        kich_thuoc_trang = kich_thuoc_trang,
        so_trang         = so_trang,
        offset           = offset,
        so_frame         = so_frame,
        dia_chi_vat_ly   = dia_chi_vat_ly,
        page_fault       = False,
    )


def dich_nhieu_dia_chi(
    danh_sach_dia_chi: list[int],
    kich_thuoc_trang:  int,
    page_table:        dict[int, int],
) -> list[KetQuaDich]:
    return [
        dich_dia_chi(dc, kich_thuoc_trang, page_table)
        for dc in danh_sach_dia_chi
    ]