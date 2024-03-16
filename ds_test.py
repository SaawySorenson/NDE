import machine
import library.sdcard
import library.mpu6050
import uos
import time
import ds18x20
import library.eeprom
import onewire

ds_pin = machine.Pin(1)
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))

roms = ds_sensor.scan()
print('Found DS devices: ', roms)

while True:
  ds_sensor.convert_temp()
  time.sleep_ms(750)
  for rom in roms:
    print(rom)
    tempC = ds_sensor.read_temp(rom)
    tempF = tempC * (9/5) +32
    print('temperature (C):', "{:.2f}".format(tempC))
    print('temperature (F):', "{:.2f}".format(tempF))
    print()
  time.sleep_ms(5)

