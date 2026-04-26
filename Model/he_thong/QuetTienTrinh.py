
import os
import logging
from dataclasses import dataclass

try:
    import psutil
    PSUTIL_CO_SAN = True
except ImportError:
    PSUTIL_CO_SAN = False

logger = logging.getLogger(__name__)

@dataclass
class ThongTinTienTrinh:
    """Thông tin của một tiến trình hệ thống."""
    pid:      int
    ten:      str        
    cpu:      float       
    ram_mb:   float       
    ram_phan_tram: float  
    trang_thai: str       
    nguoi_dung: str       

    def to_dict(self) -> dict:
        return {
            "pid":           self.pid,
            "ten":           self.ten,
            "cpu":           round(self.cpu, 1),
            "ram_mb":        round(self.ram_mb, 1),
            "ram_phan_tram": round(self.ram_phan_tram, 1),
            "trang_thai":    self.trang_thai,
            "nguoi_dung":    self.nguoi_dung,
        }


@dataclass
class KetQuaKill:
    """Kết quả sau khi kill một tiến trình."""
    pid:       int
    thanh_cong: bool
    thong_bao: str


def lay_danh_sach(
    sap_xep_theo: str = "cpu",
    giam_dan: bool = True,
    gioi_han: int = 50,
) -> list[ThongTinTienTrinh]:
    
    if not PSUTIL_CO_SAN:
        logger.warning("psutil chưa được cài. Trả về dữ liệu giả lập.")
        return _du_lieu_gia_lap()

    danh_sach = []

    for proc in psutil.process_iter(
        ["pid", "name", "cpu_percent", "memory_info",
         "memory_percent", "status", "username"]
    ):
        try:
            info = proc.info
            ram_mb = info["memory_info"].rss / (1024 * 1024) if info["memory_info"] else 0.0

            danh_sach.append(ThongTinTienTrinh(
                pid           = info["pid"],
                ten           = info["name"] or "unknown",
                cpu           = info["cpu_percent"] or 0.0,
                ram_mb        = ram_mb,
                ram_phan_tram = info["memory_percent"] or 0.0,
                trang_thai    = info["status"] or "unknown",
                nguoi_dung    = info["username"] or "unknown",
            ))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Sắp xếp
    sap_xep_hop_le = {"cpu", "ram_mb", "ten", "pid"}
    key = sap_xep_theo if sap_xep_theo in sap_xep_hop_le else "cpu"
    danh_sach.sort(key=lambda p: getattr(p, key), reverse=giam_dan)

    return danh_sach[:gioi_han]


def lay_mot(pid: int) -> ThongTinTienTrinh | None:
    
    if not PSUTIL_CO_SAN:
        return None

    try:
        proc = psutil.Process(pid)
        with proc.oneshot():
            ram_mb = proc.memory_info().rss / (1024 * 1024)
            return ThongTinTienTrinh(
                pid           = pid,
                ten           = proc.name(),
                cpu           = proc.cpu_percent(),
                ram_mb        = ram_mb,
                ram_phan_tram = proc.memory_percent(),
                trang_thai    = proc.status(),
                nguoi_dung    = proc.username(),
            )
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


def ket_thuc(pid: int) -> KetQuaKill:
    
    if not PSUTIL_CO_SAN:
        return KetQuaKill(pid, False, "psutil chưa được cài đặt")

    try:
        proc = psutil.Process(pid)
        ten  = proc.name()

        proc.terminate()                   

        try:
            proc.wait(timeout=3)           
        except psutil.TimeoutExpired:
            proc.kill()                     

        logger.info(f"Đã kill tiến trình {ten} (PID={pid})")
        return KetQuaKill(
            pid=pid,
            thanh_cong=True,
            thong_bao=f"Đã kết thúc tiến trình '{ten}' (PID={pid})"
        )

    except psutil.NoSuchProcess:
        return KetQuaKill(pid, False, f"Tiến trình PID={pid} không tồn tại")
    except psutil.AccessDenied:
        return KetQuaKill(pid, False, f"Không có quyền kill PID={pid}")
    except Exception as e:
        return KetQuaKill(pid, False, f"Lỗi: {e}")


def lay_thong_tin_he_thong() -> dict:
    """Lấy thông tin tổng quan CPU và RAM của hệ thống."""
    if not PSUTIL_CO_SAN:
        return {"cpu_tong": 0.0, "ram_tong_mb": 0, "ram_dung_mb": 0, "ram_phan_tram": 0.0}

    ram = psutil.virtual_memory()
    return {
        "cpu_tong":      psutil.cpu_percent(interval=0.1),
        "ram_tong_mb":   round(ram.total   / (1024 * 1024), 1),
        "ram_dung_mb":   round(ram.used    / (1024 * 1024), 1),
        "ram_con_mb":    round(ram.available / (1024 * 1024), 1),
        "ram_phan_tram": ram.percent,
    }

def _du_lieu_gia_lap() -> list[ThongTinTienTrinh]:
    """Trả dữ liệu mẫu để test View khi chưa cài psutil."""
    mau = [
        (1,    "systemd",   0.0,  5.2,  0.1, "running", "root"),
        (512,  "python3",  12.5, 45.3,  1.2, "running", "user"),
        (1024, "chrome",   25.0, 310.0, 8.5, "running", "user"),
        (2048, "code",      8.3, 180.0, 5.0, "running", "user"),
        (3000, "firefox",  15.2, 220.0, 6.1, "running", "user"),
        (4096, "bash",      0.1,   3.1, 0.1, "sleeping","user"),
        (5000, "vim",       0.0,   2.5, 0.1, "sleeping","user"),
    ]
    return [
        ThongTinTienTrinh(pid, ten, cpu, ram, ram_p, tt, usr)
        for pid, ten, cpu, ram, ram_p, tt, usr in mau
    ]