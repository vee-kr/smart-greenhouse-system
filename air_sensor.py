import board
import busio
import adafruit_pcf8591.pcf8591 as PCF
from adafruit_pcf8591.analog_in import AnalogIn


class MQ135Sensor:
    '''
        Class for reading CO₂ concentration values
        from the MQ135 gas sensor using the PCF8591 ADC.
    '''

    def __init__(self, r0=25.98):
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.pcf = PCF.PCF8591(self.i2c)

        self.adc_pin = AnalogIn(self.pcf, PCF.A0)

        self.R0 = r0
        self.RLOAD = 10.0
        self.V_REF = 3.3

    def get_ppm(self):
        '''
            Reads the sensor voltage and converts it
            into an approximate CO₂ concentration in ppm.
        '''

        try:

            voltage = self.adc_pin.voltage

            if voltage < 0.1:
                return 415.0  # Fresh air CO₂ baseline level
            if voltage >= self.V_REF:
                voltage = self.V_REF - 0.1

            rs = ((self.V_REF - voltage) * self.RLOAD) / voltage

            ratio = rs / self.R0

            ppm_raw = 110.47 * pow(ratio, -2.862)

            final_ppm = ppm_raw + 415.0

            return round(min(final_ppm, 5000.0), 1)

        except Exception as e:
            print(f"Error while reading sensor data: {e}")
            return None


if __name__ == "__main__":
    import time

    sensor = MQ135Sensor()
    print("Sensor initialized. Starting measurements...")
    try:
        while True:
            print(f"CO₂ concentration: {sensor.get_ppm()} ppm")
            time.sleep(2)
    except KeyboardInterrupt:
        print("Stopping...")

