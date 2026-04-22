import time
import json
import logging
import requests
import paho.mqtt.client as mqtt

# Configure System Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# --- SYSTEM CONFIGURATION ---
API_KEY = "YOUR_OPENWEATHER_API_KEY"
LAT, LON = "41.0082", "28.9784"
MQTT_BROKER = "192.168.1.100"
MQTT_PORT = 1883
POLLING_INTERVAL = 300

class RainwaterController:
    def __init__(self):
        # Operational Thresholds
        self.wind_safe_threshold = 12.5 
        self.rain_prob_threshold = 70.0 
        self.local_humidity_threshold = 85.0 

        # Edge Node Telemetry States
        self.local_humidity = 0.0
        self.local_wind = 0.0

        # MQTT Client Setup
        self.mqtt_client = mqtt.Client("CloudCollectors_Gateway")
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_message = self._on_message

    def start(self):
        try:
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
            self.mqtt_client.loop_start()
            logging.info("Hybrid Decision Engine Initialized. MQTT Connected.")
        except Exception as e:
            logging.error(f"MQTT Connection Failed: {e}")

    def _on_connect(self, client, userdata, flags, rc):
        client.subscribe("rwh/tank01/telemetry/#")

    def _on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode('utf-8'))
            
            if "humidity" in topic:
                self.local_humidity = float(payload.get("value", self.local_humidity))
            elif "wind" in topic:
                self.local_wind = float(payload.get("value", self.local_wind))
        except Exception as e:
            logging.warning(f"Payload parsing error on topic {msg.topic}: {e}")

    def fetch_weather_forecast(self):
        try:
            url = f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={API_KEY}"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            rain_prob = data['list'][0].get('pop', 0) * 100
            wind_speed = data['list'][0]['wind'].get('speed', 0)
            return rain_prob, wind_speed
        except requests.exceptions.RequestException as e:
            logging.error(f"Cloud API Fetch Error: {e}")
            return 0.0, 0.0

    def trigger_actuator(self, command):
        payload = json.dumps({"valve_cmd": command, "timestamp": int(time.time())})
        self.mqtt_client.publish("rwh/tank01/cmd/valve", payload, qos=1, retain=True)
        logging.info(f"Actuator command dispatched: {command}")

    def run_decision_cycle(self):
        api_rain_prob, api_wind = self.fetch_weather_forecast()
        
        # Determine peak wind stress between local and cloud data
        max_wind = max(api_wind, self.local_wind)

        # Priority 1: Wind-Safe Autonomous Protocol
        if max_wind > self.wind_safe_threshold:
            logging.warning(f"WIND-SAFE OVERRIDE ENGAGED! Critical Wind Detected: {max_wind} m/s")
            self.trigger_actuator("SAFE-STOW")
            return

        # Priority 2: Hybrid Decision Matrix
        if api_rain_prob > self.rain_prob_threshold and self.local_humidity > self.local_humidity_threshold:
            logging.info(f"Conditions optimal. Rain Prob: {api_rain_prob}%, Local Hum: {self.local_humidity}%")
            self.trigger_actuator("DEPLOY")
        else:
            logging.info("Conditions sub-optimal. Maintaining stow state.")
            self.trigger_actuator("STOW")

if __name__ == "__main__":
    controller = RainwaterController()
    controller.start()

    try:
        while True:
            controller.run_decision_cycle()
            time.sleep(POLLING_INTERVAL)
    except KeyboardInterrupt:
        logging.info("Interrupt received. Shutting down system securely...")
        controller.mqtt_client.loop_stop()
        controller.mqtt_client.disconnect()
