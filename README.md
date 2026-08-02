# 🪴 Smart GreenHouse System



Smart GreenHouse System is an IoT-based platform developed using Raspberry Pi 3B+.
It monitors environment conditions and automatically controls the system to help plants grow in optimal conditions.

The project combines 3D modeling, environmental sensors, a web dashboard, a Telegram Bot, a local E-paper display and computer vision into a single automated ecosystem.   

---

## 🎯 Why I built this project


Today, many people want to eat **fresh** and **healthy** food, but it isn't always easy to find this food in local supermarkets. 
Growing plants at home is really difficult for many people, because you need to constantly monitor environmental conditions: temperature, humidity and soil moisture. 

I decided to build this project to help people grow fresh herbs, mint, and other plants at home more conveniently and with minimal effort by automating routine greenhouse tasks.

---

## 🔎 Preview

### Final System

<img src="media/Final_system.jpg" alt="GitHub" width="75%">

### Telegram Bot interface

<img src="media/Telegram_Bot.jpg" alt="GitHub" width="75%">


### Website interface

<img src="media/Website.jpg" alt="GitHub" width="75%">


### E-paper Display

<img src="media/Epaper_display.jpg" alt="GitHub" width="65%">

---

## 🌟 Features

- 🌡️ Temperature and humidity monitoring
- 💧 Soil moisture monitoring
- ☀️ Light intensity monitoring
- 🌬️ CO2 concentration monitoring
- 🧊 Automatic cooling and humidification control
- 📱 Telegram Bot for control parameters and notifications
- 🌐 Web dashboard 
- 🖥️ E-paper local display
- 🤖🧠 Computer vision module (OpenCV) for plant growth analysis
- 🖨️ Custom 3D-printed enclosure
- 📊 Real-time sensor data

---

## ⚙️ Technologies

### 🖨️ 3D Design & Printing

- KOMPAS-3D (CAD)
- UltiMaker Cura
- 3D printer Dobot Mooz 3DF Plus

### ⚒️ Hardware

- Raspberry Pi 3 Model B+
- Temperature and Humidity sensor (DHT22)
- Soil Moisture sensor (YL-38)
- Light sensor (KY-018)
- Air Quality sensor (MQ-135)
- Steam generator
- Relay module
- Peltier Cooling module 
- LED Grow light
- E-paper display (Waveshare 7.5")

### 💻 Software

- Raspberry Pi GPIO
- Python
- FastAPI
- Aiogram
- HTML/CSS
- OpenCV
- JSON 

---

## 🏗 System Architecture

```text
Sensors → Raspberry Pi → JSON Database
                                ↓
              Telegram Bot / Website / E-paper display
```

All interfaces synchronize environmental data in real time through the JSON-based data exchange system.

---

## 📂Repository Structure

``` text
smart-greenhouse-system/
⏐
⏐⎯ main.py
⏐⎯ tg_bot.py
⏐⎯ e-paper.py
⏐⎯ vision_engine.py
⏐⎯ dht22_sensor.py
⏐⎯ air_sensor.py
⏐⎯ lux_sensor.py
⏐⎯ moisture_sensor.py
⏐
⏐
⏐⎯ templates/
⏐   ⏐⎯ index.html
⏐   ⏐⎯ login.html
⏐   ⏐⎯ settings.html
⏐    
⏐
⏐⎯ config.json
⏐⎯ display_template.jpg
⏐⎯ requirements.txt
⏐⎯ .env.example
⏐⎯ .gitignore
⏐⎯ README.md
```
---

## 📥 Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file using `.env.example` and configure:

```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_ID=your_telegram_user_id
PROXY=your_vpn_proxy
ADMIN_PASSWORD=your_password_for_website
```
Run the system:

```bash
python tg_bot.py
python main.py
python e-paper.py
```
---