import machine
import library.sdcard
import library.mpu6050
import uos
import time
import ds18x20
import library.eeprom

# AT24C32 on 0x50
I2C_ADDR = 0x50     # DEC 80, HEX 0x50

i2c = machine.I2C(1, scl=machine.Pin(3), sda=machine.Pin(2), freq=800000)
eeprom = library.eeprom.EEPROM(addr=I2C_ADDR, at24x=32, i2c=i2c)

print("EEPROM is on I2C address 0x{0:02x}".format(eeprom.addr))
print("EEPROM has {} pages of {} bytes".format(eeprom.pages, eeprom.bpp))
print("EEPROM size is {} bytes ".format(eeprom.capacity))

print("Save 'micropython' at address 10 ...")
eeprom.write(0, "aaaaaaaa")

print("Read 0-11")
a=eeprom.read(0,11)
print("Read:", a)


