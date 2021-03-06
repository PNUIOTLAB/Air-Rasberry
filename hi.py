from multiprocessing import Process, JoinableQueue, Queue, Manager
from http.server import BaseHTTPRequestHandler, HTTPServer
from bluepy.btle import Scanner, DefaultDelegate
import logging
import json
import time
import sys
import socket
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

flag = [0,0,0,0,0,0,0] ###자동신호
time_signal = [[(0,None),(0,None),(0,None),(0,None),(0,None),(0,None)],
               [(0,None),(0,None),(0,None),(0,None),(0,None),(0,None)],
               [(0,None),(0,None),(0,None),(0,None),(0,None),(0,None)]]

time_local = [0,0,0,0,0,0] ###자동 신호 시간 리스트

fan = [[17,17,13,13,13,13],
       [13,13,27,27,13,13],
       [13,13,13,13,22,22]] ###기기의 핀 번호
###에어컨,히터,환풍기,가습기,제습기,공기청정기

data_que = Queue()
flag_que = Queue() #자동신호 큐

ctrl_result = []    #수동신호 리스트
set_result = []    #임계값 리스트


#임계값
Threshold_humidup = [45]
Threshold_humiddown = [35]

Threshold_tempup = [26]
Threshold_tempdown = [24]

Threshold_dust1 = 200
Threshold_dust2 = 200
Threshold_Co2 = 6000


Target_device_addr = ["c3:98:3a:11:5a:38","20:20:1d:27:d1:38","ac:1a:30:f0:49:38"]


GPIO.setup(fan[0], GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(fan[1], GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(fan[2], GPIO.OUT, initial = GPIO.LOW)


class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

#    def handleDiscovery(self, dev, isNewDev, isNewData):
#        if isNewDev:
#            print("Discovered device %s" % dev.addr)
#        elif isNewData:
#            print("Recieved new data from %s", dev.addr)

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
            print("control signal: ",  ctrl_result)
            tm = time.time()
            sec = int(tm%(60*60*24))

            if ctrl_result[6]==101:
                print("signal: 101")
                for i in range(0,6):
                    if ctrl_result[i]==True:
                        time_signal[0][i] = (sec, True)
                    elif ctrl_result[i]== False:
                        time_signal[0][i] = (sec,False)
                    elif ctrl_result[i] == None:
                        time_signal[0][i] = (0, None)
                    else:
                        pass
            elif ctrl_result[6]==102:
                print("signal: 102")
                for i in range(0,6):
                    if ctrl_result[i]==True:
                        time_signal[1][i] = (sec,True)
                    elif ctrl_result[i] == False:
                        time_signal[1][i] = (sec,False)
                    elif ctrl_result[i] == None:
                        time_signal[1][i] = (0, None)
                    else:
                        pass
            elif ctrl_result[6]==103:
                print("signal: 103")
                for i in range(0,6):
                    if ctrl_result[i]==True:
                        time_signal[2][i] = (sec,True)
                    elif ctrl_result[i] == False:
                        time_signal[2][i] = (sec,False)
                    elif ctrl_result[i] == None:
                        time_signal[2][i] = (0, None)
                    else:
                        pass
            else:
                pass


        print("time0: ", time_signal[0]) 
        print("time1: ", time_signal[1])
        print("time2: ", time_signal[2])
        self._set_response()

def ble_scan():
    data_tmp = [0]*7
    scanner = Scanner().withDelegate(ScanDelegate())

    while True:
        devices = scanner.scan(10.0)
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
                        print("data in ble_scan: ", data_tmp)
         #온도 습도 초미세먼지 미세먼지 가스 시간 방 
def make_flag():
    print ("make_flag in")
    oldtemp = 25
    while True:
        Flag=[False]*14
        
        if data_que.qsize() <= 0:
            continue
        (temp,humid,micro_dust,dust,gas,time,locate)=data_que.get()

        if(temp>Threshold_tempup[0]):
            Flag[0]=True
        elif(temp<Threshold_tempdown[0]):
            Flag[1]=True

        if(humid>Threshold_humidup[0]):
            Flag[3]=True
        elif(humid<Threshold_humiddown[0]):
            Flag[2]=True

        if(gas>Threshold_Co2):
            Flag[4]=True

        if(micro_dust>Threshold_dust1 or dust>Threshold_dust2):
            Flag[5]=True

        if(int(temp-oldtemp) > 10 or int(temp) > 40):
            Flag[12]=True
            oldtemp=temp

        Flag[6]=locate
        Flag[7]=temp
        Flag[8]=humid
        Flag[9]=micro_dust
        Flag[10]=dust
        Flag[11]=gas
        Flag[13]=time
        print("Flag : ",Flag)
# Flag : 에어컨, 보일러, 가습기, 제습기, 환풍기, 공기청정기, 방 || 온도, 습도, 초미세, 미세, 가스 || 화제, 시간 
        flag_que.put(Flag)



def run(server_class=HTTPServer, handler_class=S, port=8080):
    logging.basicConfig(level=logging.INFO)
    server_address = ('192.168.0.73', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd...\n')
    httpd.serve_forever()
    #logging.info('Stopping httpd...\n')

def udp_send(tmp_flag):
    ##tmp_flag[7]에 있는 시간과 일치하는 시간의 데이터를 data store를 찾아서 엮어서 
    tmp_flag.append((Threshold_tempup[0]+Threshold_tempdown[0])/2)
    tmp_flag.append((Threshold_humidup[0]+Threshold_humiddown[0])/2)
    print ("tmp_flag in upd : ",tmp_flag)
    tmp_flag[0:5] ,tmp_flag[7:12] = tmp_flag[7:12] ,tmp_flag[0:5]
    tmp_flag.insert(11,tmp_flag.pop(5))
    before_data=",".join(map(str,tmp_flag))
    print ("type: ",type(before_data),"before_data: ",before_data)
    complete_data=before_data.replace("True","1").replace("False","0")
    print ("complete before_data in udp : ", complete_data)
    send_data=bytes(complete_data , encoding = "utf-8")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
    sock.settimeout(0)
    sock.bind(('',55555))
    sock.sendto(send_data,('192.168.0.55',2222))
#    data = sock.recvfrom(2048)
    sock.close()

def get_signal():
    from sys import argv
    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
    
def Calculation (a, Flag):
    print("Room number: ", a)
    print("flag in Calculation: ", Flag)
    check_1 = 0 #초기화
    print("signal time table", time_signal[a])

    

    ###수동제어 체크
    for i in range (0 , 6): 
        if time_signal[a][i][0] != 0:
            check_1 = 1
            break
        else:
            pass
#            check_1 = 0
#    if check_1 == 0: ### 수동제어 없었음->일반 자동신호 시행
#        print("Auto Control")
#        for i in range (0,6):
#            if Flag[i] == True:
#                #GPIO.output(fan[a], GPIO.HIGH)
#                print("fan on", i)
#            elif Flag[i] == False:
#                #GPIO.output(fan[a], GPIO.LOW)
#                print("fan off ", i)

    if check_1 == 1:
        print("Signal Control")
        for i in range (0,6): ### 자동제어 시간체크(자동 제어 시간 계산 및 리스트 완성)
            if Flag[i] == True:
                tm= time.time()
                secs = int(tm % (60*60*24))
                time_local[i] = secs
            else:
                time_local[i] = 0
                    
        for i in range (0,6): ###수동제어 - 자동제어 시간차 계산
            if time_signal[a][i][0] != 0:
                tmp1 = time_signal[a][i][0]
                tmp2 = time_local[i]
                delay = tmp2 - tmp1 ##딜레이 버려짐 /// 딜레이 확인했습니다!@
                    
                if delay < 60:
                    if time_signal[a][i][1] == True:
                        #GPIO.output(fan[a], GPIO.HIGH)
                        #print("fan on ", i)
                        Flag[i]=True
                    elif time_signal[a][i][1] == False:
                        #GPIO.output(fan[a], GPIO.LOW)
                        #print("fan off ", i)
                        Flag[i]=False

                elif delay > 60: 
#                    if Flag[i] == True:
#                        #GPIO.output(fan[a], GPIO.HIGH)
#                        print("fan on ", i)
#                    elif Flag[i] == False:
#                        #GPIO.output(fan[a], GPIO.LOW)
#                        print("fan off ", i)
                    time_signal[0][i] = (0, None)

#            elif time_signal[a][i][0] == 0:
#                if Flag[i] == True:
#                    #GPIO.output(gigi[i], GPIO.HIGH)
#                    print("fan on ", i)
#                elif Flag[i] == False:
#                    #GPIO.output(fan[a], GPIO.LOW)
#                    print("fan off ", i)
                    
    udp_send(Flag)
    print(Flag)

    for i in range(6,12):
        if Flag[i]==True:
            GPIO.output(fan[a][i-6], GPIO.HIGH)
            print ("ROOM ",a," fan ",i-6," on")
        else:
            GPIO.output(fan[a][i-6], GPIO.LOW)
 


def local_sign(): ### 자동 제어 신호 값 처리 및 연산
    
    print("local sign start")
    while True:
        if(flag_que.qsize() <= 0):
            continue
        flag = flag_que.get()

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
   
    GPIO.output(fan[0], GPIO.LOW)
    GPIO.output(fan[1], GPIO.LOW)
    GPIO.output(fan[2], GPIO.LOW)
