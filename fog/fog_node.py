import time
import threading
import json
import logging
import requests
from flask import Flask, jsonify
from flask_cors import CORS
from sensors import sensors

# Optional: Boto3 can be used if pushing directly to SQS/DynamoDB from Fog
# Using requests to hit an API Gateway is usually preferred for edge-to-cloud

app = Flask(__name__)
CORS(app) # Enable CORS for dashboard local testing
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
AGGREGATION_INTERVAL = 15  # seconds
VEHICLE_COUNT_THRESHOLD = 30  # High vehicle count threshold
SPEED_THRESHOLD = 20.0      # Low speed threshold (km/h)
POLLUTION_THRESHOLD = 150.0 # AQI threshold for pollution alert

# Cloud API Endpoint (Replace with actual AWS API Gateway /traffic-data URL after deployment)
CLOUD_API_URL = "https://woztq8wnt8.execute-api.us-east-1.amazonaws.com/prod/traffic-data"

# Initially set to False to run purely locally. 
# Toggle to True when you want to start pushing aggregated data to your AWS Cloud.
PUSH_TO_CLOUD = True
class FogNodeManager:
    def __init__(self):
        self.running = False
        self.history = [] # Store brief history for /status endpoint

    def start(self):
        self.running = True
        sensors.start()
        threading.Thread(target=self._aggregation_loop, daemon=True).start()
        logging.info("Fog Node Started. Aggregating data every 10 seconds.")

    def stop(self):
        self.running = False
        sensors.stop()

    def _aggregation_loop(self):
        while self.running:
            time.sleep(AGGREGATION_INTERVAL)
            self._process_data()

    def _process_data(self):
        # 1. Aggregate locally
        readings = sensors.get_readings()
        
        # In a real system, you might average data over the 10 seconds.
        # Here we just take the current snapshot as the 'summary' for simplicity.
        vehicle_count = readings.get("vehicle_count", 0)
        avg_speed = readings.get("average_speed", 0.0)
        noise = readings.get("noise_level", 0.0)
        pollution = readings.get("pollution_level", 0.0)

        # 2. Compute Congestion & Alerts
        congestion_alert = (vehicle_count > VEHICLE_COUNT_THRESHOLD) and (avg_speed < SPEED_THRESHOLD)
        pollution_alert = (pollution > POLLUTION_THRESHOLD)

        summary_payload = {
            "timestamp": int(time.time()),
            "node_id": "Intersection-A1",
            "metrics": {
                "average_vehicle_count": vehicle_count,
                "average_speed_kmh": avg_speed,
                "average_noise_db": noise,
                "average_pollution_aqi": pollution
            },
            "alerts": {
                "congestion": congestion_alert,
                "pollution_warning": pollution_alert
            }
        }

        self.history.insert(0, summary_payload)
        if len(self.history) > 10:
            self.history.pop()

        # Log local decision making
        log_msg = f"Aggregated: V={vehicle_count}, S={avg_speed}, CO2={pollution} | "
        if congestion_alert:
            log_msg += "[CONGESTION DETECTED] "
        if pollution_alert:
            log_msg += "[POLLUTION ALERT] "
        logging.info(log_msg)

        # 3. Send Summary to Cloud (Reduced Bandwidth)
        self._send_to_cloud(summary_payload)

    def _send_to_cloud(self, payload):
        if not PUSH_TO_CLOUD:
            logging.debug("Cloud push disabled. Payload: %s", json.dumps(payload))
            return
        
        try:
            # Send summary+alerts only
            response = requests.post(CLOUD_API_URL, json=payload, timeout=5)
            response.raise_for_status()
            logging.info("Successfully pushed summary to cloud.")
        except Exception as e:
            logging.error(f"Failed to push to cloud: {e}")

fog_manager = FogNodeManager()

@app.route('/status')
def status():
    # Local API to check node status directly
    return jsonify({
        "status": "online",
        "latest_readings": sensors.get_readings(),
        "recent_summaries": fog_manager.history[:3]
    })

if __name__ == '__main__':
    fog_manager.start()
    app.run(host='0.0.0.0', port=5001, use_reloader=False)
