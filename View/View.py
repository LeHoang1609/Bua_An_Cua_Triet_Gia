import time
class PhilosopherView:
    def __init__(self):
        self.icons = {
            "THINKING": " Thinking",
            "HUNGRY": " Hungry",
            "EATING": " Eating..."
        }

    def update_display(self, phil_id, status):
        display_text = self.icons.get(status, status)
        print(f"Philosopher {phil_id} is {display_text}")

    def log_to_file(self, message):
        with open("Data/simulation_log.txt", "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%H:%M:%S')} - {message}\n")