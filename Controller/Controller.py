from Model.Model import Philosopher, Fork
from View.View import PhilosopherView
import time

class DiningController:
    def __init__(self, num_phil=5):
        self.num_phil = num_phil
        self.view = PhilosopherView()
        self.forks = [Fork(i) for i in range(num_phil)]
        self.philosophers = []

    def on_status_change(self, phil_id, status):
        """Hàm callback để Model gọi mỗi khi triết gia đổi trạng thái"""
        self.view.update_display(phil_id, status)

    def start_simulation(self):
        print(f"--- Starting Simulation with {self.num_phil} Philosophers ---")
        
        for i in range(self.num_phil):
            left = self.forks[i]
            right = self.forks[(i + 1) % self.num_phil]
            
            p = Philosopher(i, left, right, self.on_status_change)
            self.philosophers.append(p)
        
        for p in self.philosophers:
            p.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nSimulation stopped by user.")