import machine
import library.sdcard
import library.mpu6050
import uos
import math
import time
import ds18x20
import library.eeprom
import onewire


#PINOUT
DS = 6

MPU_SDA = 2
MPU_SCL = 3
MPU_I2C = 1 #0/1

EEP_SDA = 4
EEP_SCL = 5
EEP_I2C = 0 #0/1

SD_SPI = 1 #0/1
SD_CS = 13
SD_SCK = 10
SD_MOSI = 11
SD_MISO = 12

KY = 0


#KY-031 SETUP
impact = machine.Pin(KY, machine.Pin.IN, machine.Pin.PULL_DOWN)


#MPU SETUP
# Set up the mpu I2C interface
i2c = machine.I2C(MPU_I2C, sda=machine.Pin(MPU_SDA), scl=machine.Pin(MPU_SCL))
# Set up the MPU6050 class 
mpu = library.mpu6050.MPU6050(i2c)
# wake up the MPU6050 from sleep
mpu.wake()


#SD SETUP
# Assign chip select (CS) pin (and start it high)
cs = machine.Pin(SD_CS, machine.Pin.OUT) 
# Intialize SPI peripheral (start with 1 MHz)
spi = machine.SPI(SD_SPI,
                  baudrate=1000000,
                  polarity=0,
                  phase=0,
                  bits=8,
                  firstbit=machine.SPI.MSB,
                  sck=machine.Pin(SD_SCK),
                  mosi=machine.Pin(SD_MOSI),
                  miso=machine.Pin(SD_MISO)) 
# Initialize SD card
sd = library.sdcard.SDCard(spi, cs) 
# Mount filesystem
vfs = uos.VfsFat(sd)
uos.mount(vfs, "/sd")


#EEPROM SETUP
# AT24C32 on 0x50
I2C_ADDR = 0x50     # DEC 80, HEX 0x50
i2c2 = machine.I2C(EEP_I2C, scl=machine.Pin(EEP_SCL), sda=machine.Pin(EEP_SDA), freq=800000)
eeprom = library.eeprom.EEPROM(addr=I2C_ADDR, at24x=32, i2c=i2c2)
#eeprom atributes if needed
#print("EEPROM is on I2C address 0x{0:02x}".format(eeprom.addr))
#print("EEPROM has {} pages of {} bytes".format(eeprom.pages, eeprom.bpp))
#print("EEPROM size is {} bytes ".format(eeprom.capacity))


#DS18B20 SETUP
ds_pin = machine.Pin(DS)
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))

roms = ds_sensor.scan()
#print('Found DS devices: ', roms)



class Data():   #data structure
    gyro_data = []
    accel_data = []
    temp_data = []
    time_data = []

    def __init__(self, gyro, accel, temp, time):  
        self.gyro_data = gyro 
        self.accel_data = accel
        self.temp_data = temp
        self.time_data = time

    def getgyro(self):
        return self.gyro_data

    def getaccel(self):
        return self.accel_data
    
    def gettemp(self):
        return self.temp_data
    
    def gettime(self):
        return self.time_data
        
        
        

Dataset = []       
falling = False
pointer = 0
i = 0
timeout = 3 #timeout definition in seconds, timeout/delay < ~150, more values cause memory overflow
timecount = 0
delay = 0.02  #50Hz, max 1kHz for accel, 8kHz for gyro,   
cur_speed = 0

with open("/sd/accel_data.txt", "w") as file:   #clear previous test files
    file.write("")

with open("/sd/gyro_data.txt", "w") as file:
    file.write("")

with open("/sd/temp_data.txt", "w") as file:
    file.write("")

with open("/sd/impact_data.txt", "w") as file:
    file.write("")

with open("/sd/abs_accel_data.txt", "w") as file:
        file.write("")

with open("/sd/cur_spd_data.txt", "w") as file:
        file.write("")

while True:
    #gyro/accel readout
    gyro = mpu.read_gyro_data()
    accel = mpu.read_accel_data()
    accel_tot = math.sqrt(math.pow(accel[0],2)+math.pow(accel[1],2)+math.pow(accel[2],2))   #absolute acceleration formula
    #temp readout
    ds_sensor.convert_temp()
    
   
    #freefall values, need more testing
    if(accel_tot > 1.5):
        falling = True
    
    
    if(falling):
        
        print("Gyro: " + str(gyro) + ", Accel: " + str(accel)) 
        print("Accel total", accel_tot)
        
        for rom in roms:
            tempC = ds_sensor.read_temp(rom)
            print('temperature (C):', "{:.2f}".format(tempC))
            
        Dataset.append(Data(gyro,accel,tempC,timecount))  #save to data structure
        
        #timeout break
        if timecount >= timeout:
            with open("/sd/impact_data.txt", "w") as file:
                file.write("Impact timed out")
            break 

        print("Time: ",timecount)
        timecount = timecount + delay

        #impact sensor break
        if impact.value() == 1:
            with open("/sd/impact_data.txt", "w") as file:
                file.write("Impact time" + str(timecount))
            break    
    
    
    time.sleep(delay) 



#writing data to sd and eeprom
for index, Data in enumerate(Dataset):
    with open("/sd/gyro_data.txt", "a") as file:
        file.write(str(Dataset[index].getgyro()) +"     "+ str(Dataset[index].gettime()) + "\r\n")
    with open("/sd/accel_data.txt", "a") as file:
        file.write(str(Dataset[index].getaccel()) +"     "+ str(Dataset[index].gettime()) + "\r\n")
    with open("/sd/temp_data.txt", "a") as file:
        file.write(str(Dataset[index].gettemp()) +"     "+ str(Dataset[index].gettime()) + "\r\n")
    
    abs = math.sqrt(math.pow(Dataset[index].getaccel()[0],2) + math.pow(Dataset[index].getaccel()[1],2) + math.pow(Dataset[index].getaccel()[2],2)) #absolute acceleration

    with open("/sd/abs_accel_data.txt", "a") as file:
        file.write(str(abs)+"     "+ str(Dataset[index].gettime()) + "\r\n")

    cur_speed = cur_speed + ((abs - 1) * Dataset[index].gettime())        #current speed

    with open("/sd/cur_spd_data.txt", "a") as file:
        file.write(str(cur_speed)+"     "+ str(Dataset[index].gettime()) + "\r\n")
    

    for x in range(len(str(Dataset[index].getgyro()))):     #eeprom writes, probably not enough memory, 
            eeprom.write(pointer, str(Dataset[index].getgyro())[x])
            pointer=+1
            if(pointer >= 4095):
                pointer = 0

    for x in range(len(str(Dataset[index].getaccel()))):    
            eeprom.write(pointer, str(Dataset[index].getaccel())[x])
            pointer=+1
            if(pointer >= 4095):
                pointer = 0

    for x in range(len(str(Dataset[index].gettemp()))):    
            eeprom.write(pointer, str(Dataset[index].gettemp())[x])
            pointer=+1
            if(pointer >= 4095):
                pointer = 0

uos.umount(vfs)
