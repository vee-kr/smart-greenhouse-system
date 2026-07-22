import asyncio
import logging
import datetime
import json
import time
import os
import RPi.GPIO as GPIO
import socket
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from aiogram.filters.command import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.client.session.aiohttp import AiohttpSession


try:
    from dht22_sensor import get_temperature_humidity
    from moisture_sensor import SoilSensor
    from air_sensor import MQ135Sensor
    from lux_sensor import get_light_lux
except ImportError as e:
    logging.error(f"Background process error: {e}")
    
    
current_active_mode_name = None
LIGHT_PIN = 21
STEAM_PIN = 23
PELTIER_PIN = 26
FAN_PIN = 12
DATA_FILE = '/home/vasilisa/project/smart_mushroom_sensors.json'
CONFIG_FILE = '/home/vasilisa/project/config.json'
ALERT_RETRY_INTERVAL = 3600

last_alerts_time = {"temp": 0, "hum": 0, "co2": 0, "soil": 0, "light": 0}

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup([LIGHT_PIN, STEAM_PIN, PELTIER_PIN, FAN_PIN], GPIO.OUT)
GPIO.setup(LIGHT_PIN, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(STEAM_PIN, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(PELTIER_PIN, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(FAN_PIN, GPIO.OUT, initial=GPIO.LOW)


try:
    moisture_sensor = SoilSensor(address=0x48, channel=1)
    air_sensor = MQ135Sensor(r0=25.98)
except Exception:
    moisture_sensor = None
    air_sensor = None
    logging.warning("Moisture/Air sensors were not detected.")


SCREEN_UPDATE_COOLDOWN = 60

def load_env():
    with open(".env") as f:
        for line in f:
            key, value = line.strip().split("=", 1)
            os.environ[key] = value

load_env()

TOKEN = os.environ.get("BOT_TOKEN")
admin_id = int(os.environ.get("ADMIN_ID"))

PROXY = os.environ.get("PROXY")
session = AiohttpSession(proxy=PROXY)

bot = Bot(token=TOKEN, session = session)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)



def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except: return "127.0.0.1"
    
    
def get_current_limits():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                conf = json.load(f)
            active_mode_key = conf['current_state']['active_mode']
            return conf['modes'].get(active_mode_key)
    except: return None    


def sync_read_sensors():
    res = {"t": None, "h": None, "m": 0, "c": 0, "l": 0}
    try:
        t, h = get_temperature_humidity()
        res["t"], res["h"] = t, h
    except: pass
    try:
        if moisture_sensor: res["m"] = moisture_sensor.get_moisture_percentage()
    except: pass
    try:
        if air_sensor: res["c"] = air_sensor.get_ppm()
    except Exception as e:
        logging.error(e)
    try:
        res["l"] = get_light_lux()
    except Exception as e:
        logging.error(e)
    return res



async def update_sensors_logic():
    loop = asyncio.get_running_loop()
    now = datetime.datetime.now()
    raw = await loop.run_in_executor(None, sync_read_sensors)
    sensor_data = {
        "temperature": raw["t"] if raw["t"] is not None else "--",
        "humidity": raw["h"] if raw["h"] is not None else "--",
        "soil_moisture": raw["m"],
        "co2": raw["c"],
        "light": raw["l"],
        "time": now.strftime("%H:%M:%S")
    }
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(sensor_data, f, ensure_ascii=False, indent=2)
    return sensor_data, raw["t"], raw["h"], raw["m"], raw["c"], raw["l"], now




# Periodically updates sensor readings
async def background_sensor_monitor():

    global last_alerts_time, current_active_mode_name
    while True:
        try:

            _, t, h, m, c, l, now = await update_sensors_logic()
            

            limits = get_current_limits()
            
            if limits:
                cur_ts = time.time()
                alerts_list = []
                

                new_mode_name = limits.get('name')
                if current_active_mode_name is not None and new_mode_name != current_active_mode_name:
                    change_msg = (
                        f"🔄 <b>MODE CHANGED!</b>\n"
                        f"Previous mode: <s>{current_active_mode_name}</s>\n"
                        f"New mode: <b>{new_mode_name}</b>\n"
                        f"──────────────────\n"
                        f"🎯 Target: {limits.get('temp_target')}°C / {limits.get('humidity_target')}%"
                    )
                    await bot.send_message(admin_id, change_msg, parse_mode="HTML")
                

                current_active_mode_name = new_mode_name


                light_h = limits.get('light_hours', 0)
                if light_h > 0 and (8 <= now.hour < 8 + light_h):
                    GPIO.output(LIGHT_PIN, GPIO.HIGH)
                else:
                    GPIO.output(LIGHT_PIN, GPIO.LOW)


                t_target = limits.get('temp_target')
                t_thresh = limits.get('temp_threshold', 2.0)
                
                if t is not None:
                    if t > (t_target + t_thresh):
                        GPIO.output(PELTIER_PIN, GPIO.HIGH)
                        GPIO.output(FAN_PIN, GPIO.HIGH)
                        if cur_ts - last_alerts_time['temp'] > ALERT_RETRY_INTERVAL:
                            alerts_list.append(f"🌡 Overheating: {t}°C. Cooling enabled ❄️")
                            last_alerts_time['temp'] = cur_ts
                    elif t < t_target:
                        GPIO.output(PELTIER_PIN, GPIO.LOW)
                        GPIO.output(FAN_PIN, GPIO.LOW)
                        last_alerts_time['temp'] = 0


                h_target = limits.get('humidity_target')
                if h is not None:
                    if h < (h_target - 5):
                        GPIO.output(STEAM_PIN, GPIO.HIGH)
                        if cur_ts - last_alerts_time['hum'] > ALERT_RETRY_INTERVAL:
                            alerts_list.append(f"💧 Low humidity: {h}%. Humidifier enabled 💨")
                            last_alerts_time['hum'] = cur_ts
                    elif h >= h_target:
                        GPIO.output(STEAM_PIN, GPIO.LOW)
                        last_alerts_time['hum'] = 0


                co2_max = limits.get('co2_max')
                if co2_max and c > co2_max and cur_ts - last_alerts_time['co2'] > ALERT_RETRY_INTERVAL:
                    alerts_list.append(f"🌬 High CO2 level: {c} PPM")
                    last_alerts_time['co2'] = cur_ts
                
                if m is not None and m < 20 and cur_ts - last_alerts_time['soil'] > ALERT_RETRY_INTERVAL:
                    alerts_list.append(f"🪴 Dry soil detected: {m}%")
                    last_alerts_time['soil'] = cur_ts

                # ALERT
                if alerts_list:
                    msg = (f"🚨 <b>CONTROL ALERT: {new_mode_name}</b>\n"
                           f"──────────────────\n" + "\n".join(alerts_list) +
                           f"\n──────────────────\n⏰ {now.strftime('%H:%M:%S')}")
                    await bot.send_message(admin_id, msg, parse_mode="HTML")

            logging.info("Climate monitoring completed.")
        except Exception as e:
            logging.error(f"Background process error: {e}")
        
        await asyncio.sleep(600) # Check every 10 minutes


# KEYBOARDS
def main_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📊 Sensor data"),
        KeyboardButton(text="⚙️ Equipment"),
        KeyboardButton(text="🎮 Control panel")
    )
    builder.row(
        KeyboardButton(text="📝 Fill out the form"),
        KeyboardButton(text="👨‍💻 Support")
    )
    builder.row(KeyboardButton(text="📸 Take a photo"))
    return builder.as_markup(resize_keyboard=True, input_field_placeholder="Choose a section...")

def devices_inline_kb():
    l_st = "🟢" if GPIO.input(LIGHT_PIN) else "🔴"
    s_st = "🟢" if GPIO.input(STEAM_PIN) else "🔴"
    p_st = "🟢" if GPIO.input(PELTIER_PIN) else "🔴"

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"Light {l_st}", callback_data="toggle_light"),
            InlineKeyboardButton(text=f"Steam {s_st}", callback_data="toggle_steam")
        ],
        [
            InlineKeyboardButton(text=f"Cooling (Peltier + fans) {p_st}", callback_data="toggle_cooling")
        ]
    ])

def link_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Contact administrator ✉️", url='https://t.me/vee_kr')]
    ])


# HANDLERS
@dp.message(Command('start'))
async def command_start(message: Message):
    welcome_text = (
        "<b>🌿 Welcome to SmartMushroom!</b>\n"
        "──────────────────────────\n"
        "I am your personal assistant for managing the smart greenhouse. 👋🏻\n\n"
        "<b>What I can do:</b>\n"
        "• Monitor real-time sensor data.\n"
        "• Provide information about greenhouse modules.\n"
        "• Help you contact the developer.\n"
        "• Collect feedback through forms.\n\n"
        "<i>Use the menu buttons below to get started.</i>"
    )
    await message.answer(welcome_text, reply_markup=main_kb(), parse_mode="HTML")



@dp.message(F.text == '⚙️ Equipment')
async def info_handler(message: Message):
    info_text = (
        "<b>🏗 TECHNICAL SPECIFICATION</b>\n"
        "──────────────────────────\n"
        "🤖 <b>Controller:</b> <code>Raspberry Pi 3B</code>\n"
        "🔌 <b>Control board:</b> <code>Breadboard</code>\n\n"
        "<b>📡 Installed sensors:</b>\n"
        "• <b>Climate:</b> DHT-22 (temperature and humidity)\n"
        "• <b>Soil climate:</b> YL-018 (soil moisture)\n"
        "• <b>Gas:</b> MQ-135 (CO2 level)\n"
        "• <b>Light:</b> KY-018 (photoresistor)\n\n"
        "<b>❄️ Cooling:</b> Peltier module (TEC-1) + active fan ventilation.\n"
        "<b>💧 Humidity control:</b> Steam generator\n"
        "──────────────────────────\n"
        "<i>💡 Tip: Keep the growing medium fresh to support better growth!</i>"
    )
    await message.answer(info_text, parse_mode="HTML")



@dp.message(F.text == '🎮 Control panel')
async def control_menu_handler(message: Message):
    l_state = "ON 🟢" if GPIO.input(LIGHT_PIN) else "OFF 🔴"
    s_state = "ON 🟢" if GPIO.input(STEAM_PIN) else "OFF 🔴"
    p_state = "OFF 🔴" if not GPIO.input(PELTIER_PIN) else "ON 🟢"

    await message.answer(
        f"<b>🕹 Greenhouse module control</b>\n\n"
        f"Lighting: {l_state}\n"
        f"Humidifier: {s_state}\n"
        f"Cooling: {p_state}",
        reply_markup=devices_inline_kb(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("toggle_"))
async def process_toggle(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]

    if action == "light":
        GPIO.output(LIGHT_PIN, not GPIO.input(LIGHT_PIN))
    elif action == "steam":
        GPIO.output(STEAM_PIN, not GPIO.input(STEAM_PIN))
    elif action == "cooling":
        new_state = not GPIO.input(PELTIER_PIN)
        GPIO.output(PELTIER_PIN, new_state)
        GPIO.output(FAN_PIN, new_state)

    await callback.answer("State changed!")

    l_state = "ON 🟢" if GPIO.input(LIGHT_PIN) else "OFF 🔴"
    s_state = "ON 🟢" if GPIO.input(STEAM_PIN) else "OFF 🔴"
    p_state = "OFF 🔴" if not GPIO.input(PELTIER_PIN) else "ON 🟢"

    await callback.message.edit_text(
        f"<b>🕹 Greenhouse module control</b>\n\n"
        f"Lighting: {l_state}\n"
        f"Humidifier: {s_state}\n"
        f"Cooling: {p_state}",
        reply_markup=devices_inline_kb(),
        parse_mode="HTML"
    )



@dp.message(F.text == '📊 Sensor data')
async def sensors_handler(message: Message):
    if not os.path.exists(DATA_FILE):
        await message.answer("⚠️ Sensor data file not found yet.")
        return

    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        await message.answer(f"⚠️ Could not read sensor data: {e}")
        return

    temp = data.get("temperature", "--")
    hum = data.get("humidity", "--")
    soil = data.get("soil_moisture", "--")
    co2 = data.get("co2", "--")
    light = data.get("light", "--")
    time_value = data.get("time", "--")

    temp_text = f"{temp}°C" if temp != "--" else "--"
    hum_text = f"{hum}%" if hum != "--" else "--"
    soil_text = f"{soil}%" if soil != "--" else "--"
    co2_text = f"{co2} PPM" if co2 != "--" else "--"
    light_text = f"{light} lm" if light != "--" else "--"

    # CO2 status
    if isinstance(co2, (int, float)):
        if co2 < 800:
            status_co2 = "✅ Air quality is excellent"
        elif co2 < 1200:
            status_co2 = "⚠️ Air feels stale, consider ventilation"
        else:
            status_co2 = "🚨 URGENT: High CO2 level detected!"
    else:
        status_co2 = "⚠️ CO2 sensor data unavailable"

    # Light status
    if isinstance(light, (int, float)):
        if light < 50:
            light_status = "🌑 Very dark"
        elif light < 450:
            light_status = "💡 Normal indoor lighting"
        else:
            light_status = "☀️ Bright"
    else:
        light_status = "⚠️ Light sensor data unavailable"

    # Soil status
    if isinstance(soil, (int, float)):
        if soil < 30:
            soil_status = "⚠️ Soil is too dry"
        elif soil <= 70:
            soil_status = "✅ Soil moisture is normal"
        else:
            soil_status = "💧 Too much water"
    else:
        soil_status = "⚠️ Soil sensor data unavailable"

    report = (
        "<b>📊 SENSOR DATA</b>\n"
        "──────────────────────────\n"
        f"🌡 <b>Temperature:</b> <code>{temp_text}</code>\n"
        f"💧 <b>Air humidity:</b> <code>{hum_text}</code>\n"
        f"🪴 <b>Soil moisture:</b> <code>{soil_text}</code>\n"
        f"Status: {soil_status}\n"
        "──────────────────────────\n"
        f"🌬 <b>CO2 level:</b> <code>{co2_text}</code>\n"
        f"Status: {status_co2}\n"
        f"🌤️ <b>Light:</b> <code>{light_text}</code>\n"
        f"Status: {light_status}\n"
        "──────────────────────────\n"
        f"⏰ <b>Measurement time:</b> <code>{time_value}</code>"
    )

    await message.answer(report, parse_mode="HTML")


@dp.message(F.text == '📸 Take a photo')
async def send_photo_handler(message: Message):
    wait_msg = await message.answer("📸 Taking a photo...")

    photo_path = "test_shot.jpg"
    exit_code = os.system(f"fswebcam -d /dev/video0 -r 1280x720 --no-banner {photo_path}")
    if exit_code == 0:
        photo = types.FSInputFile(photo_path)
        await message.answer_photo(
            photo,
            caption=f"✅ Test photo\n⏰ Time: {datetime.datetime.now().strftime('%H:%M:%S')}"
        )
    else:
        await message.answer("❌ Camera error! Check if it is connected via USB.")


# FORM FSM
class Register(StatesGroup):
    name = State()
    model = State()
    mark = State()

@dp.message(F.text == '📝 Fill out the form')
async def register_start(message: Message, state: FSMContext):
    await state.set_state(Register.name)
    await message.answer("Step 1: Enter your <b>name</b>:", parse_mode="HTML")

@dp.message(Register.name)
async def register_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Register.model)
    await message.answer("Step 2: Enter the greenhouse <b>model</b>:", parse_mode="HTML")

@dp.message(Register.model)
async def register_model(message: Message, state: FSMContext):
    await state.update_data(model=message.text)
    await state.set_state(Register.mark)
    await message.answer("Step 3: Rate the usability from 1 to 10:", parse_mode="HTML")

@dp.message(Register.mark)
async def register_finish(message: Message, state: FSMContext):
    await state.update_data(mark=message.text)
    data = await state.get_data()
    await message.answer(f"✅ Thank you, {data['name']}! Your response has been received.", reply_markup=main_kb())
    await state.clear()

@dp.message(F.text == '👨‍💻 Support')
async def admin_handler(message: Message):
    await message.answer("☎️ Contact the developer:", reply_markup=link_kb())




async def main():
    asyncio.create_task(background_sensor_monitor())
    ip = get_ip_address()
    try:
        await bot.send_message(
            admin_id,
            f"🔌 <b>Power is on!</b> SmartMushroom has started successfully.\nIP: <code>{ip}</code>",
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Failed to send startup message: {e}")
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        GPIO.cleanup()
