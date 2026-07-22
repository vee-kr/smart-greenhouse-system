import logging
import datetime
import json
import os
import socket
import time
from waveshare_epd import epd7in5
from PIL import Image, ImageDraw, ImageFont
import RPi.GPIO as GPIO

# --- SETTINGS ---
DATA_FILE = '/home/vasilisa/project/smart_mushroom_sensors.json'
TEMPLATE_PATH = 'display_template.jpg'
CHECK_INTERVAL = 60 # Interval for checking updates in seconds

logging.basicConfig(level=logging.INFO)

def get_ip_address():
    """Current IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1 (No network)"

def get_data_from_json():
    """Sensor data and last file modification time"""
    if os.path.exists(DATA_FILE):
        try:
            mtime = os.path.getmtime(DATA_FILE)
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f), mtime
        except Exception as e:
            logging.error(f"JSON reading error: {e}")
    
    return {
        "temperature": "--",
        "humidity": "--",
        "soil_moisture": "--",
        "co2": "--",
        "light": "--",
        "time": "No data"
    }, 0

def draw_and_update(data, ip_addr):
    """Draw data on the e-paper display"""
    try:
        epd = epd7in5.EPD()
        epd.init() 
        
        try:
            image = Image.open(TEMPLATE_PATH).convert('1')
        except FileNotFoundError:
            logging.error(f"File '{TEMPLATE_PATH}'  was not found!")
            image = Image.new('1', (epd.width, epd.height), 255)

        draw = ImageDraw.Draw(image)


        try:
            font_title = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 35)
            font_data = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 30)
            font_link = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 22)
        except:
            font_title = font_data = font_link = ImageFont.load_default()


        draw.text((50, 30), "GREENHOUSE MONITORING", font=font_title, fill=0)
        draw.line((55, 80, 500, 80), fill=0, width=3) 

        draw.text((44, 95), f" Temperature: {data.get('temperature', '--')} °C", font=font_data, fill=0)
        draw.text((44, 130), f" Humidity: {data.get('humidity', '--')} %", font=font_data, fill=0)
        draw.text((44, 165), f" Soil: {data.get('soil_moisture', '--')} %", font=font_data, fill=0)
        draw.text((50, 200), f"☁ CO2: {data.get('co2', '--')} ppm", font=font_data, fill=0)
        draw.text((50, 235), f"☀ Light: {data.get('light', '--')} lm", font=font_data, fill=0)
        
        draw.text((52, 270), f"Measurement time: {data.get('time', 'No data')}", font=font_link, fill=0)


        draw.rectangle((40, 400, 550, 450), outline=0, width=2) 
        draw.text((52, 310), "Control website:", font=font_data, fill=0)
        draw.text((53, 345), f"http://{ip_addr}:8000", font=font_link, fill=0)


        logging.info(f"Drawing display image... (IP: {ip_addr})")
        epd.display(epd.getbuffer(image))
        

        epd.sleep()
        logging.info("Display is in sleep mode.")

    except Exception as e:
        logging.error(f"Display error: {e}")

def main():
    logging.info("Waiting for network connection...")
    
    last_mtime = 0
    last_ip = ""
    
    logging.info("Monitoring script started. Waiting for data...")

    while True:
        current_data, current_mtime = get_data_from_json()
        current_ip = get_ip_address()


        if current_mtime > last_mtime or current_ip != last_ip:
            if current_ip != last_ip:
                logging.info(f"IP changed: {last_ip} -> {current_ip}")
            else:
                logging.info("JSON file was updated")

            draw_and_update(current_data, current_ip)
            

            last_mtime = current_mtime
            last_ip = current_ip
        
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Script stopped")
        GPIO.cleanup()
