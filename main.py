import sys
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from View.MainWindow         import MainWindow
from Controller.ControllerTrietGia import ControllerTrietGia
from Controller.ControllerCPU      import ControllerCPU
from Controller.ControllerBoNho    import ControllerBoNho
from Controller.ControllerTaskMgr  import ControllerTaskMgr


def main():
    # ── 1. Tạo MainWindow (chứa toàn bộ View) ────────────────────────────
    app = MainWindow()

    # ── 2. Lấy từng View con ─────────────────────────────────────────────
    view_triet_gia  = app._frames["ViewTrietGia"]
    view_cpu        = app._frames["ViewCPU"]
    view_bo_nho     = app._frames["ViewBoNho"]
    view_task_mgr   = app._frames["ViewTaskManger"]

    # ── 3. Tạo Controller và gắn vào View ────────────────────────────────
    ctrl_triet_gia = ControllerTrietGia(view_triet_gia)
    view_triet_gia.controller = ctrl_triet_gia

    ctrl_cpu = ControllerCPU(view_cpu)
    view_cpu.controller = ctrl_cpu

    ctrl_bo_nho = ControllerBoNho(view_bo_nho)
    view_bo_nho.controller = ctrl_bo_nho

    ctrl_task_mgr = ControllerTaskMgr(view_task_mgr)
    view_task_mgr.controller = ctrl_task_mgr

    # ── 4. Chạy ──────────────────────────────────────────────────────────
    app.run()


if __name__ == "__main__":
    main()