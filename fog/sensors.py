import random
import time
import threading

class SensorSimulator:
    def __init__(self):
        self.lock = threading.Lock()
        self.current_data = {
            "vehicle_count": 0,
            "average_speed": 0.0,
            "noise_level": 0.0,
            "pollution_level": 0.0
        }
        self.running = False

    def start(self):
        self.running = True
        threading.Thread(target=self._simulate_vehicle_count, daemon=True).start()
        threading.Thread(target=self._simulate_average_speed, daemon=True).start()
        threading.Thread(target=self._simulate_noise_level, daemon=True).start()
        threading.Thread(target=self._simulate_pollution_level, daemon=True).start()

    def stop(self):
        self.running = False

    def get_readings(self):
        with self.lock:
            return self.current_data.copy()

    def _simulate_vehicle_count(self):
        # Number of vehicles passing per interval
        while self.running:
            with self.lock:
                # Simulate between 0 and 50 vehicles passing in a short interval
                # High number means high volume
                self.current_data["vehicle_count"] = random.randint(5, 45)
            time.sleep(2)

    def _simulate_average_speed(self):
        # Simulated vehicle speed in km/h
        while self.running:
            with self.lock:
                # Correlate roughly with vehicle count: high count -> lower speed
                count = self.current_data.get("vehicle_count", 20)
                if count > 30:
                    speed = random.uniform(5.0, 20.0) # Slow traffic
                else:
                    speed = random.uniform(30.0, 60.0) # Normal traffic
                self.current_data["average_speed"] = round(speed, 2)
            time.sleep(2)

    def _simulate_noise_level(self):
        # Traffic noise in dB
        while self.running:
            with self.lock:
                # Typical city traffic noise 70-85 dB
                # Heavy traffic might reach 90+ dB
                count = self.current_data.get("vehicle_count", 20)
                if count > 30:
                    noise = random.uniform(80.0, 95.0)
                else:
                    noise = random.uniform(60.0, 75.0)
                self.current_data["noise_level"] = round(noise, 2)
            time.sleep(2)

    def _simulate_pollution_level(self):
        # Simulated pollution level (CO2 Air Quality Index)
        # Assuming scale 0-500 where > 150 is unhealthy (alert)
        while self.running:
            with self.lock:
                count = self.current_data.get("vehicle_count", 20)
                speed = self.current_data.get("average_speed", 40.0)
                # Congestion (high count, low speed) increases pollution
                if count > 30 and speed < 20.0:
                    # Gradually increase pollution during congestion
                    current = self.current_data.get("pollution_level", 100.0)
                    pollution = min(500.0, current + random.uniform(5.0, 20.0))
                else:
                    # Gradually decrease
                    current = self.current_data.get("pollution_level", 100.0)
                    pollution = max(0.0, current - random.uniform(2.0, 10.0))
                
                # Add some random noise
                pollution += random.uniform(-5.0, 5.0)
                self.current_data["pollution_level"] = round(max(0.0, pollution), 2)
            time.sleep(2)

# Global sensor instance
sensors = SensorSimulator()
