import smbus2
import time

class SoilSensor:
    def __init__(self, address=0x48, channel=1):
        self.bus = smbus2.SMBus(1)
        self.address = address
        self.channel = channel

        # Calibration values for dry and wet soil
        self.DRY_VALUE = 165
        self.WET_VALUE = 80

    def get_raw_value(self):
        try:
            self.bus.write_byte(self.address, 0x40 + self.channel)

            # Discard the first unstable reading
            self.bus.read_byte(self.address)

            return self.bus.read_byte(self.address)

        except Exception as e:
            print(f"Reading error: {e}")
            return None

    def get_moisture_percentage(self):
        raw = self.get_raw_value()

        if raw is None:
            return 0

        # Convert raw sensor value into soil moisture percentage (0-100%)
        percentage = ((self.DRY_VALUE - raw) / (self.DRY_VALUE - self.WET_VALUE)) * 100

        return max(0, min(100, round(percentage, 1)))

    def get_status_text(self, percentage):
        if percentage < 30:
            return "❌ The soil is too dry! Watering is needed"
        elif 30 <= percentage <= 70:
            return "✅ The soil moisture level is normal"
        else:
            return "🌊 Too much water detected!"

