# 🌱 Smart Greenhouse System

Smart Greenhouse System is an IoT-based greenhouse monitoring and automation platform developed using Raspberry Pi.
The project combines environmental sensors, automation modules, computer vision, a Telegram bot, a web dashboard, and an e-paper display into one synchronized ecosystem.

The system continuously monitors greenhouse conditions, stores sensor data in a shared JSON architecture, and provides real-time access through multiple interfaces.

---

## ✨ Main Features

* 🌡 Real-time temperature and humidity monitoring
* 🪴 Soil moisture analysis
* 🌬 CO₂ concentration monitoring
* 💡 Light intensity monitoring
* 🤖 Telegram bot for greenhouse control and notifications
* 🌐 Web dashboard for monitoring and management
* 📟 E-paper display with live environmental data
* 🧠 Computer vision module based on OpenCV
* ❄️ Automatic cooling and humidification control
* 📊 Historical data logging
* 🖨 Custom 3D-printed enclosure and structural components

---

## 🏗 System Architecture

```text
Sensors → Raspberry Pi → Shared JSON Database
                              ↓
Telegram Bot / Web Dashboard / E-paper Display
```

The project uses a centralized JSON-based data exchange system.
All interfaces display synchronized environmental information in real time.

---

## ⚙️ Technologies Used

### Hardware

* Raspberry Pi 3B
* DHT22 temperature and humidity sensor
* YL-018 soil moisture sensor
* MQ-135 air quality sensor
* KY-018 photoresistor
* Peltier cooling module
* Steam generator
* E-paper display

### Software

* Python
* FastAPI
* Aiogram
* OpenCV
* Raspberry Pi GPIO
* HTML/CSS
* JSON architecture

---

## 📸 Interfaces

### Telegram Bot

* Real-time sensor monitoring
* Equipment control
* Alerts and notifications
* Greenhouse management tools

### Web Dashboard

* Live environmental monitoring
* Device control panel
* Growth progress tracking
* Administrative settings

### E-paper Display

* Standalone low-power monitoring screen
* Live environmental data visualization

---

## 🧠 Computer Vision

The project includes a computer vision module developed with OpenCV.
Image segmentation in HSV color space is used to estimate crop growth and analyze greenhouse conditions.

---

## 📂 Repository Structure

```text
smart-greenhouse-system/
│
├── tg_bot.py
├── main.py
├── e-paper.py
├── vision_engine.py
├── air_sensor.py
├── dht22_sensor.py
├── lux_sensor.py
├── moisture_sensor.py
│
├── templates/
│   ├── index.html
│   ├── login.html
│   └── settings.html
│
├── requirements.txt
├── config.json
├── .env.example
└── .gitignore
```

---

## 🚀 Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file using `.env.example` and configure:

```env
BOT_TOKEN=your_token
ADMIN_ID=your_id
PROXY=your_proxy
ADMIN_PASSWORD=your_password
```

Run the system:

```bash
python tg_bot.py
python main.py
python e-paper.py
```

---

## 📁 Additional Materials

Additional project materials are available in Google Drive:

* 3D models
* Technical drawings
* Wiring diagrams
* Demonstration videos
* Photos of the assembled system
* Project documentation

[Google Drive Folder](PASTE_YOUR_LINK_HERE)

---

## 🎥 Demonstration

The repository includes:

* Telegram bot demonstration
* Web dashboard demonstration
* Real sensor monitoring examples

---

## 👩‍💻 Author

Developed by Vasilisa Krivtsova
GitHub: https://github.com/vee-kr

---

