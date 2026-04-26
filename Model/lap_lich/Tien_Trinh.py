
from dataclasses import dataclass, field


@dataclass
class TienTrinh:
    

    ten:          str
    burst_time:   int
    arrival_time: int = 0
    priority:     int = 0

    def __post_init__(self):
        if self.burst_time <= 0:
            raise ValueError(f"burst_time phải > 0, nhận được: {self.burst_time}")
        if self.arrival_time < 0:
            raise ValueError(f"arrival_time phải >= 0, nhận được: {self.arrival_time}")


@dataclass
class KetQuaTienTrinh:

    ten:               str
    arrival_time:      int
    burst_time:        int
    thoi_diem_bat_dau: int
    thoi_diem_ket_thuc: int

    @property
    def waiting_time(self) -> int:
        return self.turnaround_time - self.burst_time

    @property
    def response_time(self) -> int:
        return self.thoi_diem_bat_dau - self.arrival_time

    @property
    def turnaround_time(self) -> int:
        return self.thoi_diem_ket_thuc - self.arrival_time

    def to_dict(self) -> dict:
        return {
            "ten":               self.ten,
            "arrival_time":      self.arrival_time,
            "burst_time":        self.burst_time,
            "bat_dau":           self.thoi_diem_bat_dau,
            "ket_thuc":          self.thoi_diem_ket_thuc,
            "waiting_time":      self.waiting_time,
            "response_time":     self.response_time,
            "turnaround_time":   self.turnaround_time,
        }


@dataclass
class KhoangGantt:
    ten:       str  
    bat_dau:   int  
    ket_thuc:  int   

    def to_dict(self) -> dict:
        return {
            "ten":      self.ten,
            "bat_dau":  self.bat_dau,
            "ket_thuc": self.ket_thuc,
        }