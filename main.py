from Controller.Controller import DiningController
import os
import sys


def prepare_environment():
    """Tạo thư mục Data nếu chưa có để tránh lỗi ghi file"""
    if not os.path.exists('Data'):
        os.makedirs('Data')

if __name__ == "__main__":
    prepare_environment()
    
    app = DiningController(num_phil=5)
    app.start_simulation()
