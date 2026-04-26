
from dataclasses import dataclass, field
from copy import deepcopy
from .Tien_Trinh import TienTrinh, KetQuaTienTrinh, KhoangGantt


@dataclass
class KetQuaLapLich:
    thuat_toan:   str
    gantt:        list[KhoangGantt]
    ket_qua:      list[KetQuaTienTrinh]

    @property
    def avg_waiting_time(self) -> float:
        if not self.ket_qua:
            return 0.0
        return round(sum(k.waiting_time for k in self.ket_qua) / len(self.ket_qua), 2)

    @property
    def avg_response_time(self) -> float:
        if not self.ket_qua:
            return 0.0
        return round(sum(k.response_time for k in self.ket_qua) / len(self.ket_qua), 2)

    @property
    def avg_turnaround_time(self) -> float:
        if not self.ket_qua:
            return 0.0
        return round(sum(k.turnaround_time for k in self.ket_qua) / len(self.ket_qua), 2)

    def to_dict(self) -> dict:
        return {
            "thuat_toan":        self.thuat_toan,
            "gantt":             [g.to_dict() for g in self.gantt],
            "ket_qua":           [k.to_dict() for k in self.ket_qua],
            "avg_waiting_time":  self.avg_waiting_time,
            "avg_response_time": self.avg_response_time,
            "avg_turnaround":    self.avg_turnaround_time,
        }


def fcfs(danh_sach: list[TienTrinh]) -> KetQuaLapLich:
    """
    First Come First Served.
    Sắp xếp theo arrival_time, chạy từng tiến trình đến hết.
    """
    tien_trinh = sorted(deepcopy(danh_sach), key=lambda p: (p.arrival_time, p.ten))
    gantt      = []
    ket_qua    = []
    thoi_gian  = 0

    for p in tien_trinh:
        if thoi_gian < p.arrival_time:
            gantt.append(KhoangGantt("idle", thoi_gian, p.arrival_time))
            thoi_gian = p.arrival_time

        bat_dau   = thoi_gian
        ket_thuc  = thoi_gian + p.burst_time
        gantt.append(KhoangGantt(p.ten, bat_dau, ket_thuc))
        ket_qua.append(KetQuaTienTrinh(
            ten=p.ten,
            arrival_time=p.arrival_time,
            burst_time=p.burst_time,
            thoi_diem_bat_dau=bat_dau,
            thoi_diem_ket_thuc=ket_thuc,
        ))
        thoi_gian = ket_thuc

    return KetQuaLapLich("FCFS", gantt, ket_qua)

def sjf(danh_sach: list[TienTrinh]) -> KetQuaLapLich:
    """
    Shortest Job First (non-preemptive).
    Tại mỗi thời điểm CPU rảnh, chọn tiến trình có burst_time nhỏ nhất
    trong số đã đến hàng đợi.
    """
    con_lai   = sorted(deepcopy(danh_sach), key=lambda p: p.arrival_time)
    gantt     = []
    ket_qua   = []
    thoi_gian = 0
    hang_doi  = []    

    while con_lai or hang_doi:
        while con_lai and con_lai[0].arrival_time <= thoi_gian:
            hang_doi.append(con_lai.pop(0))

        if not hang_doi:
            thoi_gian_nhay = con_lai[0].arrival_time
            gantt.append(KhoangGantt("idle", thoi_gian, thoi_gian_nhay))
            thoi_gian = thoi_gian_nhay
            continue

        hang_doi.sort(key=lambda p: (p.burst_time, p.ten))
        p = hang_doi.pop(0)

        bat_dau  = thoi_gian
        ket_thuc = thoi_gian + p.burst_time
        gantt.append(KhoangGantt(p.ten, bat_dau, ket_thuc))
        ket_qua.append(KetQuaTienTrinh(
            ten=p.ten,
            arrival_time=p.arrival_time,
            burst_time=p.burst_time,
            thoi_diem_bat_dau=bat_dau,
            thoi_diem_ket_thuc=ket_thuc,
        ))
        thoi_gian = ket_thuc

    return KetQuaLapLich("SJF", gantt, ket_qua)

def priority(danh_sach: list[TienTrinh]) -> KetQuaLapLich:
    """
    Priority Scheduling (non-preemptive).
    Số priority nhỏ hơn = ưu tiên cao hơn.
    Tại mỗi thời điểm CPU rảnh, chọn tiến trình có priority nhỏ nhất.
    """
    con_lai   = sorted(deepcopy(danh_sach), key=lambda p: p.arrival_time)
    gantt     = []
    ket_qua   = []
    thoi_gian = 0
    hang_doi  = []

    while con_lai or hang_doi:
        while con_lai and con_lai[0].arrival_time <= thoi_gian:
            hang_doi.append(con_lai.pop(0))

        if not hang_doi:
            thoi_gian_nhay = con_lai[0].arrival_time
            gantt.append(KhoangGantt("idle", thoi_gian, thoi_gian_nhay))
            thoi_gian = thoi_gian_nhay
            continue
        hang_doi.sort(key=lambda p: (p.priority, p.arrival_time))
        p = hang_doi.pop(0)

        bat_dau  = thoi_gian
        ket_thuc = thoi_gian + p.burst_time
        gantt.append(KhoangGantt(p.ten, bat_dau, ket_thuc))
        ket_qua.append(KetQuaTienTrinh(
            ten=p.ten,
            arrival_time=p.arrival_time,
            burst_time=p.burst_time,
            thoi_diem_bat_dau=bat_dau,
            thoi_diem_ket_thuc=ket_thuc,
        ))
        thoi_gian = ket_thuc

    return KetQuaLapLich("Priority", gantt, ket_qua)

def round_robin(danh_sach: list[TienTrinh], quantum: int = 2) -> KetQuaLapLich:
    """
    Round Robin.

    Tham số:
        danh_sach : danh sách tiến trình
        quantum   : time quantum (ms), mặc định 2
    """
    if quantum <= 0:
        raise ValueError("quantum phải > 0")

    @dataclass
    class _ThongTin:
        p:            TienTrinh
        con_lai:      int
        bat_dau_dau:  int = -1     

    thong_tin = {
        p.ten: _ThongTin(deepcopy(p), p.burst_time)
        for p in danh_sach
    }

    con_lai_chua_den = sorted(deepcopy(danh_sach), key=lambda p: p.arrival_time)
    hang_doi: list[str] = []    
    gantt     = []
    thoi_gian = 0
    while con_lai_chua_den and con_lai_chua_den[0].arrival_time <= thoi_gian:
        hang_doi.append(con_lai_chua_den.pop(0).ten)

    while hang_doi or con_lai_chua_den:
        if not hang_doi:
            thoi_gian_nhay = con_lai_chua_den[0].arrival_time
            gantt.append(KhoangGantt("idle", thoi_gian, thoi_gian_nhay))
            thoi_gian = thoi_gian_nhay
            while con_lai_chua_den and con_lai_chua_den[0].arrival_time <= thoi_gian:
                hang_doi.append(con_lai_chua_den.pop(0).ten)
            continue

        ten = hang_doi.pop(0)
        tt  = thong_tin[ten]

        if tt.bat_dau_dau == -1:
            tt.bat_dau_dau = thoi_gian

        thoi_gian_chay = min(tt.con_lai, quantum)
        bat_dau  = thoi_gian
        ket_thuc = thoi_gian + thoi_gian_chay
        gantt.append(KhoangGantt(ten, bat_dau, ket_thuc))
        tt.con_lai  -= thoi_gian_chay
        thoi_gian    = ket_thuc

        moi_den = []
        while con_lai_chua_den and con_lai_chua_den[0].arrival_time <= thoi_gian:
            moi_den.append(con_lai_chua_den.pop(0).ten)

        if tt.con_lai > 0:
            hang_doi.extend(moi_den)
            hang_doi.append(ten)
        else:
            hang_doi.extend(moi_den)

    ket_qua = []
    for ten, tt in thong_tin.items():
        ket_thuc_cuoi = max(
            g.ket_thuc for g in gantt if g.ten == ten
        )
        ket_qua.append(KetQuaTienTrinh(
            ten=ten,
            arrival_time=tt.p.arrival_time,
            burst_time=tt.p.burst_time,
            thoi_diem_bat_dau=tt.bat_dau_dau,
            thoi_diem_ket_thuc=ket_thuc_cuoi,
        ))

    ket_qua.sort(key=lambda k: k.arrival_time)

    return KetQuaLapLich(f"Round Robin (q={quantum})", gantt, ket_qua)