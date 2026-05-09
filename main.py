import os
import json
import uvicorn
import csv
import asyncio
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from vision_engine import analyze_growth
from datetime import datetime


# --- GPIO INITIALIZATION ---
# Pins: 21-Light, 23-Steam, 26-Peltier, 12-Fan
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    PINS = [21, 23, 26, 12]
    GPIO.setup(PINS, GPIO.OUT, initial=GPIO.LOW)
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False
    print("Demo mode: GPIO not found")

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- GLOBAL VARIABLES ---
current_growth_percent = 0
DATA_FILE = "smart_mushroom_sensors.json"
CONFIG_FILE = "config.json"
LOG_FILE = "mushroom_history.csv"


def load_env():
    with open(".env") as f:
        for line in f:
            key, value = line.strip().split("=", 1)
            os.environ[key] = value

load_env()

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

def load_config():
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

config_data = load_config()
modes = config_data["modes"]

state = {
    "devices": {"light": False, "humidifier": False, "cooling": False},
    "settings": {"target_temp": 18.0, "target_hum": 85, "target_co2": 800, "current_stage": "Loading..."}
}

def get_sensor_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"temperature": 0, "humidity": 0, "soil_moisture": 0, "co2": 0, "light": 0, "time": "Waiting..."}

# --- BACKGROUND LOGIC  ---

# Background tasks:
# 1. Computer vision growth analysis
# 2. Write data to CSV
def periodic_tasks():
    global current_growth_percent
    active_mode_key = config_data["current_state"]["active_mode"]
    mode_name = modes.get(active_mode_key, {}).get("name", "Mushrooms")
    
    result = analyze_growth(mode_name)
    if result is not None:
        current_growth_percent = result

    data = get_sensor_data()
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Timestamp', 'Temp', 'Hum', 'CO2', 'Growth%'])
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M"), 
                         data.get('temperature'), data.get('humidity'),
                         data.get('co2'), current_growth_percent])

@app.on_event("startup")
async def start_periodic_tasks():
    async def task_loop():
        while True:
            periodic_tasks()
            await asyncio.sleep(60) # Repeat every minute
    asyncio.create_task(task_loop())

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if HAS_GPIO:
        state["devices"]["light"] = bool(GPIO.input(21))
        state["devices"]["humidifier"] = bool(GPIO.input(23))
        state["devices"]["cooling"] = bool(GPIO.input(26))
    try:
        start_date_str = config_data["current_state"]["start_date"]
        active_mode_key = config_data["current_state"]["active_mode"]
        

        current_mode_name = modes.get(active_mode_key, {}).get("name", "Greenhouse")
        total_days = modes.get(active_mode_key, {}).get("cycle_days", 1)
        
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        days_passed = (datetime.now() - start_date).days
        percent = min(100, int((days_passed / total_days) * 100)) if days_passed >= 0 else 0
    except:
        current_mode_name = "Greenhouse"
        days_passed, total_days, percent = 0, 1, 0

    return templates.TemplateResponse("index.html", {
        "request": request, 
        "data": get_sensor_data(), 
        "devices": state["devices"],
        "progress": {"passed": days_passed, "total": total_days, "percent": percent},
        "current_mode_name": current_mode_name
    })

@app.get("/api/status")
async def get_status():
    return {
        "growth": current_growth_percent,
        "mode": config_data["current_state"]["active_mode"]
    }

@app.get("/api/data")
async def get_api_data():
    return JSONResponse(content=get_sensor_data())

@app.post("/control")
async def control(device: str = Form(...), action: str = Form(...)):
    is_on = (action == "on")
    state["devices"][device] = is_on
    if HAS_GPIO:
        level = GPIO.HIGH if is_on else GPIO.LOW
        pin_map = {"light": 21, "humidifier": 23, "cooling": [26, 12]}
        target = pin_map.get(device)
        if isinstance(target, list):
            for p in target: GPIO.output(p, level)
        else:
            GPIO.output(target, level)
    return RedirectResponse(url="/", status_code=303)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(password: str = Form(...)):
    if password == ADMIN_PASSWORD:
        response = RedirectResponse(url="/settings", status_code=303)
        response.set_cookie(key="is_admin", value="true")
        return response
    return RedirectResponse(url="/login", status_code=303)

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    active_key = config_data["current_state"]["active_mode"]
    state["settings"]["current_stage"] = modes.get(active_key, {}).get("name", "Not selected")
    
    return templates.TemplateResponse("settings.html", {
        "request": request, 
        "modes": modes, 
        "settings": state["settings"]
    })

@app.post("/set_mode")
async def set_mode(mode_key: str = Form(...)):
    if mode_key in modes:
        config_data["current_state"]["active_mode"] = mode_key
        config_data["current_state"]["start_date"] = datetime.now().strftime("%Y-%m-%d")
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
    return RedirectResponse(url="/", status_code=303)

@app.post("/update_params")
async def update_params(temp: float = Form(...), hum: int = Form(...), co2: int = Form(...)):
    state["settings"].update({"target_temp": temp, "target_hum": hum, "target_co2": co2, "current_stage": "Manual Mode"})
    return RedirectResponse(url="/settings", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)