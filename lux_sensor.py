from smbus2 import SMBus

# I2C address of the ADC device
DEVICE_ADDRESS = 0x48

# Analog input channel for the light sensor
AIN2 = 0x42


def get_light_lux():
    try:
        with SMBus(1) as bus:
            bus.write_byte(DEVICE_ADDRESS, AIN2)

            # Discard the first unstable reading
            bus.read_byte(DEVICE_ADDRESS)

            raw = bus.read_byte(DEVICE_ADDRESS)

            # Invert the value because brighter light lowers resistance
            inverted = 255 - raw

            # Apply calibration offset
            lux_raw = inverted - 20

            if lux_raw < 0:
                lux_raw = 0

            # Convert raw value into approximate lux units
            lux = lux_raw * 4.0

            return round(lux, 1)

    except Exception as e:
        print(f"Reading error: {e}")
        return None
