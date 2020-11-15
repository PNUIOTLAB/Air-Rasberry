from multiprocessing import Process, JoinableQueue, Queue
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from bluepy.btle import Scanner, DefaultDelegate
import logging
import json
import time
import sys
import struct
###import RPi.GPIO as GPIO

###GPIO.setmode(GPIO,BCM)
###GPIO.setwarnings(False)
signal=[0,0,0,0,0,0,0] ###수동제어 신호
flag = [0,0,0,0,0,0,0] ###자동신호

time_signal = [[0,0,0,0,0,0],
               [0,0,0,0,0,0],
               [0,0,0,0,0,0]]

time_local = [0,0,0,0,0,0] ###자동 신호 시간 리스트

gigi = [17,27,18,23,24,22] ###기기의 핀 번호
###에어컨,히터,환풍기,가습기,제습기,공기청정기

data_que = JoinableQueue()
ctrl_que = JoinableQueue() #수동신호 큐
flag_que = JoinableQueue() #자동신호 큐

ctrl_result = []    #수동신호 리스트
set_result = []    #임계값 리스트

#임계값
Threshold_humidup = [45]
Threshold_humiddown = [35]

Threshold_tempup = [28]
Threshold_tempdown = [22]

Threshold_dust1 = 80
Threshold_dust2 = 35
Threshold_Co2 = 1000

#
Target_device_addr = ["c3:98:3a:11:5a:38","20:20:1d:27:d1:38","ac:1a:30:f0:49:38"]


"""
GPIO.setup(aircon, GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(heater, GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(fan, GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(humidifier, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(dehumidifier, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(aircleaner, GPIO.OUT, initial=GPIO.LOW)"""


class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            print("Discovered device %s" % dev.addr)
        elif isNewData:
            print("Recieved new data from %s", dev.addr)


class S(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
    """
    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        self._set_response()
        self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))
    """
    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        data = post_data.decode('utf-8')

        if  len(data)<=30:
            setting = json.loads(data)
            set_result = [setting['0'],setting['1']]

            if set_result[0]!=0:
                Threshold_tempup[0] = set_result[0]+1
                Threshold_tempdown[0] = set_result[0]-1
                print("tempup: ",Threshold_tempup[0])
                print("tempdown: ", Threshold_tempdown[0])
            else:
                pass

            if set_result[1]!=0:
                Threshold_humidup[0] = set_result[1]+5
                Threshold_humiddown[0] = set_result[1]-5
                print("humiup: ", Threshold_humidup[0])
                print("humidown: ", Threshold_humiddown[0])
            else:
                pass
            
            
        else:
            ctrl = json.loads(data)
            ctrl_result = [ctrl['0'],ctrl['1'],ctrl['2'],ctrl['3'],ctrl['4'],ctrl['5'],ctrl['6']]
            ctrl_que.put(ctrl_result)
            
       # print("time0: ", time_signal[0]) 
       # print("time1: ", time_signal[1])
       # print("time2: ", time_signal[2])
        self._set_response()

def ble_scan():
    data_tmp = [0]*7
    scanner = Scanner().withDelegate(ScanDelegate())
    devices = scanner.scan(0.5)
    
    for dev in devices:
        if dev.addr in Target_device_addr:
            print("Device %s (%s), RSSI=%d DB" % (dev.addr, dev.addrType, dev.rssi))
            for (adtype, desc, value) in dev.getScanData():
                if desc == "Manufacturer":
                    print ("   %s = %s" % (desc, value))
                    data_tmp[0] = float(str(int(value[0]+value[1],16))+'.'+str(int(value[2]+value[3],16)))
                    data_tmp[1] = float(str(int(value[4]+value[5],16))+'.'+str(int(value[6]+value[7],16)))
                    data_tmp[2] = int(value[8]+value[9],16)
                    data_tmp[3] = int(value[10]+value[11],16)
                    data_tmp[4] = float(str(int(value[-6]+value[-5]+value[-4]+value[-3],16))+'.'+str(int(value[-2]+value[-1],16)))
                    data_tmp[5] = time.strftime('%Y-%m-%d %H:%M:%S')
                    if dev.addr =="c3:98:3a:11:5a:38": 
                        data_tmp[6] = 102
                    elif dev.addr =="ac:1a:30:f0:49:38":
                        data_tmp[6] = 101
                    elif dev.addr =="20:20:1d:27:d1:38":
                        data_tmp[6] = 103
                    print (data_tmp)
                    data_que.put(data_tmp)

def make_flag():
    print ("make_flag in")
    oldtemp = 25
    while True:
        Flag=[False]*9
        if(data_que.qsize() <= 0):
            continue
        (temp,humid,micro_dust,dust,gas,time,locate)=data_que.get()
        
        if(temp>Threshold_tempup[0]):
            Flag[0]=True
        elif(temp<Threshold_tempdown[0]):
            Flag[1]=True

        if(humid>Threshold_humidup[0]):
            Flag[2]=True
        elif(humid<Threshold_humiddown[0]):
            Flag[3]=True

        if(gas>Threshold_Co2):
            Flag[4]=True

        if(micro_dust>Threshold_dust1 or dust>Threshold_dust2):
            Flag[5]=True

        if(int(temp-oldtemp) > 10 or int(temp) > 40):
            Flag[7]=True
            oldtemp=temp
       
        Flag[6]=locate
        Flag[8]=time
        print("Flag : ",Flag)
# Flag : 에어컨, 보일러, 가습기, 제습기, 환풍기, 공기청정기, 방, 화제, 시간
        flag_que.put(Flag)

def run(server_class=HTTPServer, handler_class=S, port=8080):
    logging.basicConfig(level=logging.INFO)
    server_address = ('192.168.0.73', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd...\n')
    httpd.serve_forever()
    #logging.info('Stopping httpd...\n')

def get_signal():
    from sys import argv
    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
    
def Calculation (a, Flag):
    print("a: ", a)
    if(ctrl_que.qsize() > 0):
        signal = ctrl_que.get()
        ctrl_que.task_done()
        tm = time.time()
        sec = int(tm%(60*60*24))
            
        if signal[6]==101:
            print("101")
            for i in range(0,6):
                if signal[i]==True:
                    time_signal[0][i] = (sec, True)
                elif signal[i]== False:
                    time_signal[0][i] = (sec,False)
                elif signal[i] == None:
                    time_signal[0][i] = (0, None)
                else:
                    pass
        elif signal[6]==102:
            print("102")
            for i in range(0,6):
                if signal[i]==True:
                    time_signal[1][i] = (sec,True)
                elif signal[i] == False:
                    time_signal[1][i] = (sec,False)
                elif signal[i] == None:
                    time_signal[1][i] = (0, None)
                else:
                    pass
        elif signal[6]==103:
            print("103")
            for i in range(0,6):
                if signal[i]==True:
                    time_signal[2][i] = (sec,True)
                elif signal[i] == False:
                    time_signal[2][i] = (sec,False)
                elif signal[i] == None:
                    time_signal[2][i] = (0, None)
                else:
                    pass
        else:
            pass

    print("signal: ", signal)
    print("flag in cal: ", Flag)
    check_1 = 0 #초기화
    print("time", time_signal[a])
    ###수동제어 체크
    for i in range (0 , 6):
        if time_signal[a][i] != 0:
            check_1 = 1
            break
        else:
            check_1 = 0
    print(check_1)
    if check_1 == 0: ### 수동제어 없었음->일반 자동신호 시행
        print("auto control")
        for i in range (0,6):
            if Flag[i] == True:
                ###GPIO.output(gigi[i], GPIO.HIGH)
                print("gigi on ",i)
            if Flag[i] == False:
                ###GPIO.output(gigi[i], GPIO.LOW)
                print("gigi off ", i)

    elif check_1 == 1:
        for i in range (0,6): ### 자동제어 시간체크(자동 제어 시간 계산 및 리스트 완성)
            if Flag[i] == True:
                tm= time.time()
                secs = int(tm % (60*60*24))
                time_local[i] = secs
            else:
                time_local[i] = 0
                    
        print("signal check")
        for i in range (0,6): ###수동제어 - 자동제어 시간차 계산
            if time_signal[a][i][0] != 0:
                tmp1 = time_signal[a][i][0]
                tmp2 = time_local[i]
                delay = tmp2 - tmp1 ##딜레이 버려짐 /// 딜레이 확인했습니다!@
                    
                if delay < 10:
                    if time_signal[a][i][1] == True:
                        ###GPIO.output(gigi[i], GPIO.HIGH)
                        print("gigi on ", i)
                    elif time_signal[a][i][1] == False:
                        ###GPIO.output(gigi[i], GPIO.LOW)
                        print("gigi off ", i)

                elif delay > 10: 
                    if Flag[i] == True:
                        ###GPIO.output(gigi[i], GPIO.HIGH)
                        print("gigi on ", i)
                    elif Flag[i] == False:
                        ###GPIO.output(gigi[i], GPIO.LOW)
                        print("gigi off ", i)
                    time_signal[0][i] = (0, None) 
                                            
            elif time_signal[a][i][0] == 0:
                if Flag[i] == True:
                    ###GPIO.output(gigi[i], GPIO.HIGH)
                    print("gigi on ", i)
                elif Flag[i] == False:
                    ###GPIO.output(gigi[i], GPIO.LOW)
                    print("gigi off ", i)

    



def local_sign(): ### 자동 제어 신호 값 처리 및 연산
    
    while True:
        if(flag_que.qsize() <=0 ):
            continue
        flag = flag_que.get()
        flag_que.task_done()
        print("get flag: ", flag)

        if flag[6] == 101:
            a=0
            Calculation (a, flag)
        if flag[6] == 102:
            a=1
            Calculation (a, flag)
        if flag[6] == 103:
            a=2
            Calculation (a, flag)
        

if __name__ == '__main__':

    th1 = Process(target=ble_scan)
    th2 = Process(target=make_flag)
    th3 = Process(target=local_sign)
    th4 = Process(target=get_signal)

    th1.start()
    th2.start()
    th3.start()
    th4.start()

    print("start\n")
    
    th1.join()
    th2.join()
    th3.join()
    th4.join()
    data_que.join()
    ctrl_que.join()
    flag_que.join()
