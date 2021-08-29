from bluepy.btle import Scanner, DefaultDelegate
import time
import sys

Target_device_addr = ["20:20:1d:27:d1:17", "ac:1a:30:f0:49:8c"]

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            print("Discovered device", dev.addr)
        elif isNewData:
            print("Recieved new data from", dev.addr) 

print ("Scan Start")
scanner = Scanner().withDelegate(ScanDelegate())
data_tmp = [0]*7


while True:
    devices = scanner.scan(5.0)
    for dev in devices:
        if dev.addr in Target_device_addr:
            print("Devices %s (%s), RSSI=%d dB" % (dev.addr, dev.addrType, dev.rssi))
            for (adtype, desc, value) in dev.getScanData():
                if desc == "Manufacturer":
                    print("  %s = %s " % (desc, value))
                    data_tmp[0] = float(str(int(value[0]+value[1], 16))+'.'+str(int(value[2]+value[3], 16)))
                    data_tmp[1] = float(str(int(value[4]+value[5], 16))+'.'+str(int(value[6]+value[7], 16)))
                    data_tmp[2] = int(value[8]+value[9]+value[10]+value[11], 16)
                    data_tmp[3] = int(value[12]+value[13]+value[14]+value[15], 16)
                    data_tmp[4] = float(str(int(value[-6]+value[-5]+value[-4]+value[-3], 16))+'.'+str(int(value[-2]+value[-1], 16)))
                    data_tmp[5] = time.strftime('%Y-%m-%d %H:%M:%S')
                    if dev.addr == "c3:98:3a:11:5a:38":
                       data_tmp[6] = 101
                    elif dev.addr == "ac:1a:30:f0:49:8c":
                       data_tmp[6] = 102
                    elif dev.addr == "20:20:1d:27:d1:17":
                       data_tmp[6] = 103
                    print (data_tmp)

