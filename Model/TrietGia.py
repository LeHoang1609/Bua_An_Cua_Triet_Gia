"""
philosopher.py - Luồng (thread) của một triết gia
"""

import threading
import time
import random
import logging
from typing import TYPE_CHECKING

from .TrietGia_State import State, Solution, PhilosopherStats

if TYPE_CHECKING:
    from .BanAnToi import BanAnTrieuGia

logger = logging.getLogger(__name__)


# ── Hằng số thời gian ──────────────────────────────────────────────
THINK_MIN, THINK_MAX = 1.0, 3.0
EAT_MIN, EAT_MAX = 1.0, 2.5
STARVATION_THRESHOLD = 8.0
DEADLOCK_TIMEOUT = 5.0


class Philosopher(threading.Thread):
    def __init__(self, ma_triet_gia: int, ban_an: "BanAnTrieuGia", giai_phap: Solution):
        super().__init__(name=f"Philosopher-{ma_triet_gia}", daemon=True)

        self.ma_triet_gia = ma_triet_gia
        self.ban_an = ban_an
        self.giai_phap = giai_phap

        self.trang_thai = State.THINKING
        self.thong_ke = PhilosopherStats(philosopher_id=ma_triet_gia)

        # Fork trái/phải
        self.id_trai = ma_triet_gia
        self.id_phai = (ma_triet_gia + 1) % ban_an.num_philosophers

        self._su_kien_dung = threading.Event()

    def run(self):
        logger.info(f"P{self.ma_triet_gia} bắt đầu [{self.giai_phap.value}]")
        while not self._su_kien_dung.is_set():
            self._suy_nghi()
            if self._su_kien_dung.is_set():
                break
            self._doi_va_an()

    def stop(self):
        self._su_kien_dung.set()

    def _suy_nghi(self):
        self._dat_trang_thai(State.THINKING)
        self.thong_ke.mark_think_start()

        thoi_gian = random.uniform(THINK_MIN, THINK_MAX) / self.ban_an.speed_factor
        self._ngu_co_the_ngat(thoi_gian)

        self.thong_ke.mark_think_end()

    def _doi_va_an(self):
        self._dat_trang_thai(State.HUNGRY)
        self.thong_ke.mark_hungry_start()

        self._kiem_tra_starvation()

        da_lay = self._lay_dua()

        if not da_lay or self._su_kien_dung.is_set():
            return

        self._dat_trang_thai(State.EATING)
        self.thong_ke.mark_eat_start()

        thoi_gian = random.uniform(EAT_MIN, EAT_MAX) / self.ban_an.speed_factor
        self._ngu_co_the_ngat(thoi_gian)

        self.thong_ke.mark_eat_end()

        self._tha_dua()

    def _lay_dua(self) -> bool:
        if self.giai_phap == Solution.NAIVE:
            return self._lay_naive()
        elif self.giai_phap == Solution.RESOURCE_HIERARCHY:
            return self._lay_theo_thu_tu()
        elif self.giai_phap == Solution.ARBITRATOR:
            return self._lay_theo_quan_ly()
        elif self.giai_phap == Solution.CHANDY_MISRA:
            return self._lay_chandy_misra()
        raise ValueError("Giải pháp không hợp lệ")

    def _lay_naive(self) -> bool:
        dua_trai = self.ban_an.forks[self.id_trai]
        dua_phai = self.ban_an.forks[self.id_phai]

        self._dat_trang_thai(State.WAITING)

        dua_trai.acquire()
        dua_trai.held_by = self.ma_triet_gia
        self.ban_an.notify_change()

        thanh_cong = dua_phai.acquire(timeout=DEADLOCK_TIMEOUT / self.ban_an.speed_factor)

        if thanh_cong:
            dua_phai.held_by = self.ma_triet_gia
            self.ban_an.notify_change()
            return True

        dua_trai.release()
        self.thong_ke.deadlock_escapes += 1
        self.ban_an.deadlock_count += 1
        self.ban_an.notify_change()

        logger.warning(f"P{self.ma_triet_gia} DEADLOCK → thả đũa")
        return False

    def _lay_theo_thu_tu(self) -> bool:
        dau = min(self.id_trai, self.id_phai)
        sau = max(self.id_trai, self.id_phai)

        dua_dau = self.ban_an.forks[dau]
        dua_sau = self.ban_an.forks[sau]

        self._dat_trang_thai(State.WAITING)

        dua_dau.acquire()
        dua_dau.held_by = self.ma_triet_gia

        dua_sau.acquire()
        dua_sau.held_by = self.ma_triet_gia

        self.ban_an.notify_change()
        return True

    def _lay_theo_quan_ly(self) -> bool:
        dua_trai = self.ban_an.forks[self.id_trai]
        dua_phai = self.ban_an.forks[self.id_phai]

        self._dat_trang_thai(State.WAITING)

        self.ban_an.waiter_semaphore.acquire()

        dua_trai.acquire()
        dua_trai.held_by = self.ma_triet_gia

        dua_phai.acquire()
        dua_phai.held_by = self.ma_triet_gia

        self.ban_an.notify_change()
        return True
    def _lay_chandy_misra(self) -> bool:
        self._dat_trang_thai(State.WAITING)

        dua_trai = self.ban_an.forks[self.id_trai]
        dua_phai = self.ban_an.forks[self.id_phai]

        self._yeu_cau_dua(dua_trai)
        if self._su_kien_dung.is_set():
            return False

        self._yeu_cau_dua(dua_phai)

        dua_trai.held_by = self.ma_triet_gia
        dua_phai.held_by = self.ma_triet_gia

        dua_trai.dirty = False
        dua_phai.dirty = False

        self.ban_an.notify_change()
        return True
    def _yeu_cau_dua(self, dua):
        cond = self.ban_an.fork_conditions[dua.fork_id]
        with cond:
            while dua.held_by is not None and not self._su_kien_dung.is_set():
                self.ban_an.fork_requests[dua.fork_id].add(self.ma_triet_gia)
                cond.wait(timeout=0.5)
    def _tha_dua(self):
        if self.giai_phap == Solution.ARBITRATOR:
            self._tha_quan_ly()
        elif self.giai_phap == Solution.CHANDY_MISRA:
            self._tha_chandy_misra()
        else:
            self._tha_don_gian()

    def _tha_don_gian(self):
        for fid in (self.id_trai, self.id_phai):
            self.ban_an.forks[fid].release()
        self.ban_an.notify_change()

    def _tha_quan_ly(self):
        for fid in (self.id_trai, self.id_phai):
            self.ban_an.forks[fid].release()
        self.ban_an.waiter_semaphore.release()
        self.ban_an.notify_change()

    def _tha_chandy_misra(self):
        for fid in (self.id_trai, self.id_phai):
            f = self.ban_an.forks[fid]
            cond = self.ban_an.fork_conditions[fid]

            with cond:
                f.dirty = True
                req = self.ban_an.fork_requests[fid]

                if req:
                    next_owner = next(iter(req))
                    req.discard(next_owner)
                    f.held_by = None
                    f.dirty = False
                    cond.notify_all()
                else:
                    f.release()

        self.ban_an.notify_change()
    def _dat_trang_thai(self, st: State):
        self.trang_thai = st
        self.ban_an.notify_change()

    def _ngu_co_the_ngat(self, t: float):
        self._su_kien_dung.wait(timeout=t)

    def _kiem_tra_starvation(self):
        cho = self.thong_ke.current_wait_time()
        if cho >= STARVATION_THRESHOLD:
            self.thong_ke.starvation_events += 1
            self.ban_an.starvation_count += 1

    def to_dict(self):
        return {
            "id": self.ma_triet_gia,
            "state": self.trang_thai.value,
            "left": self.id_trai,
            "right": self.id_phai,
            "stats": self.thong_ke.to_dict(),
        }