import adafruit_dht
import board
import time

# GPIO pin connected to the DHT22 sensor
DHT_PIN = board.D19

# Initialize the DHT22 sensor
dht_device = adafruit_dht.DHT22(DHT_PIN)

def get_temperature_humidity():
    try:
        temperature = dht_device.temperature
        humidity = dht_device.humidity

        # Return values only if valid sensor data was received
        if temperature is not None and humidity is not None:
            return temperature, humidity
        else:
            return None, None

    except RuntimeError as error:
        # Handle temporary sensor reading errors
        print(f"Reading error: {error.args[0]}")
        return None, None

    except Exception as error:
        # Release sensor resources before raising critical errors
        dht_device.exit()
        raise error
