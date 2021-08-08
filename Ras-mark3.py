from multiprocessing import Process, JoinableQueue, Queue, Manager
from http.server import BaseHTTPRequestHandler, HTTPServer
from bluepy.btle import Scanner, DefaultDelegate
import logging
import json
import time
import sys
import socket
import RPi.GPIO as GPIO
#import string


# 라즈베리 GPIO 활성
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# 자동 제어 신호
flag = [0,0,0,0,0,0,0]

# 제어 신호의 수동, 자동 변환 시간 
time_signal = [[(0,None),(0,None),(0,None),(0,None),(0,None),(0,None)], #BLE1
               [(0,None),(0,None),(0,None),(0,None),(0,None),(0,None)]] #BLE2

# 자동 제어 신호 시간 리스트
time_local = [0,0,0,0,0,0]

# 제어 장치 [에어컨, 히터, 제습기, 가습기,공기청정기, 환풍기]
device = [[17,27,13,13,13,22],  # BLE1은 에어컨, 히터, 환풍기 시연
          [13,13,16,20,21,13]]  # BLE2는 제습기, 가습기, 공기청정기 시연

data_que = Queue() # 환경요소 데이터 큐
flag_que = Queue() # 자동 제어신호 큐
ctrl_que = Queue()
thres_que = Queue() 
send_que = Queue()

ctrl_result = []    #수동신호 리스트
signal_result = []
set_result = []    #임계값 리스트
send_result = []

#임계값 [BLE1, BLE2]
std_humid = [50,50]

std_tempup = [25, 25]

std_dust1 = [200]
std_dust2 = [200]
std_Co2 = [6000]

Target_device_addr = ["20:20:1d:27:d1:17", "ac:1a:30:f0:49:8c"]


GPIO.setup(device[0][0], GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(device[0][1], GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(device[0][5], GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(device[1][2], GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(device[1][3], GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(device[1][4], GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(13, GPIO.OUT, initial = GPIO.LOW)



class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)
        print("init")

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

    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        self._set_response()
        self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        data = post_data.decode('utf-8')

        if  len(data)<=30:
            setting = json.loads(data)
            set_result = [setting['Room'], setting['set_humid'], setting['set_temp']]
            print("Room, temp, humid", set_result)
            if set_result[1]!=0:
                thres_que.put((set_result[0], set_result[1], "humid"))
            
            elif set_result[2]!=0:
                thres_que.put((set_result[0], set_result[2], "temp"))
            
            
        else:
            ctrl = json.loads(data)
            ctrl_result = [params['Room'],params['AC'],params['Boiler'],params['Dehumidifier'], # 기기별 제어 신호 
                           params['Humidifier'],params['Aircleaner'],params['Fan']]
            
            ctrl_que.put(ctrl_result)
            
            print("control signal: ",  ctrl_result)

        self._set_response()

def ble_scan():
    data_tmp = [0]*7
    scanner = Scanner().withDelegate(ScanDelegate())
    
    print(" SCAN START")

    while True:
        print("SCANNING......")
        devices = scanner.scan(5.0)
        for dev in devices:
            print("check")
            if dev.addr in Target_device_addr:
                print("===============================================================")
                print("Device %s (%s), RSSI=%d DB" % (dev.addr, dev.addrType, dev.rssi))
                for (adtype, desc, value) in dev.getScanData():
                    if desc == "Manufacturer":
                        print ("\n\n   %s = %s\n\n" % (desc, value))
                        data_tmp[0] = float(str(int(value[0]+value[1],16))+'.'+str(int(value[2]+value[3],16)))
                        data_tmp[1] = float(str(int(value[4]+value[5],16))+'.'+str(int(value[6]+value[7],16)))
                        
                        data_tmp[2] = int(value[8]+value[9]+value[10]+value[11],16)
                        data_tmp[3] = int(value[12]+value[13]+value[14]+value[15],16)
#                        print ("\n\ndata_tmp[2] : ",data_tmp[2],"\n\ndata_tmp[3] : ",data_tmp[3],"\n\n")
                        data_tmp[4] = float(str(int(value[-6]+value[-5]+value[-4]+value[-3],16))+'.'+str(int(value[-2]+value[-1],16)))
                        data_tmp[5] = time.strftime('%Y%m%d%H%M%S')
                        if dev.addr == "ac:1a:30:f0:49:8c":
                            data_tmp[6] = 101
                        elif dev.addr == "20:20:1D:27:D1:38":
                            data_tmp[6] = 102
                        data_que.put(data_tmp)
                        print("data in ble_scan: ", data_tmp)
         #온도 습도 초미세먼지 미세먼지 가스 시간 방 
    print("SCAN END")


def make_flag():
#    print ("make_flag in")
    oldtemp = 25
    while True:
        Flag=[False]*16
        if thres_que.qsize() > 0:
             (room, data, type)=thres_que.get()
             data=int(data)
             print ("Room", room,"\n manual flag data ", data," type ", type,"\n")
             if type == "humid":
                 
                 if room == '101':
                     std_humid[0] = data
                 elif room == '102':
                     std_humid[1] = data
                 
             elif type == "temp":

                 if room == '101':
                     std_temp[0] = data
                 elif room == '102':
                     std_temp[1] = data
                 
        if data_que.qsize() <= 0:
            continue
        
        (temp, humid, micro_dust, dust, gas, time, room)=data_que.get()

        if room == '101':
            i = 0
        elif locate == '102':
            i = 1
        
        if(temp > std_temp[i]+1):
            print ("Threshold tempup: ", std_temp[i]+1) 
            Flag[7]=True
        elif(temp < std_temp[i]-1):
            print ("Threshold tempdown: ",std_temp[i]-1)
            Flag[8]=True

        if(humid > std_humid[i]+10):
            Flag[9]=True
        elif(humid < std_humid[i]-10):
            Flag[10]=True

        if(micro_dust > std_dust1 or dust > std_dust2):
            Flag[11]=True

        if(gas > std_Co2):
            Flag[12]=True

        if(int(temp-oldtemp) > 10 or float(temp) >= 40.0):
            Flag[13]=True
            oldtemp=temp

        Flag[0] = time
        Flag[1] = room
        Flag[2] = temp
        Flag[3] = humid
        Flag[4] = dust
        Flag[5] = micro_dust
        Flag[6] = gas
        Flag[14] = std_temp[i]
        Flag[15] = std_humid[i]
        print("Flag : ",Flag)
        
# Flag : 시간 방 온도 습도 미세 초미세 Co2 || 에어컨 보일러 제습기 가습기 공기청정기 환풍기 || 화재 기준온도 기준습도
        flag_que.put(Flag)


def run(server_class=HTTPServer, handler_class=S, port=5000):
    logging.basicConfig(level=logging.INFO)
    server_address = ('192.168.0.26', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd...\n')
    httpd.serve_forever()
    #logging.info('Stopping httpd...\n')



def udp_send(tmp_flag):
    '''
    ##tmp_flag[7]에 있는 시간과 일치하는 시간의 데이터를 data store를 찾아서 엮어서 
    tmp_flag.append((Threshold_tempup[0]+Threshold_tempdown[0])/2)
    tmp_flag.append((Threshold_humidup[0]+Threshold_humiddown[0])/2)
#    print ("tmp_flag in upd : ",tmp_flag)
    tmp_flag[0:5] ,tmp_flag[7:12] = tmp_flag[7:12] ,tmp_flag[0:5]
    tmp_flag.insert(11,tmp_flag.pop(5))
    '''
    before_data=",".join(map(str,tmp_flag))
#    print ("type: ",type(before_data),"before_data: ",before_data)
    complete_data=before_data.replace("True","1").replace("False","0")
    print ("data which send to sever by udp : ", complete_data)
    send_data=bytes(complete_data , encoding = "utf-8")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
    sock.settimeout(0)
    sock.bind(('',55555))
    sock.sendto(send_data,('192.168.0.27',9000))
#    data = sock.recvfrom(2048)
    sock.close()
# Flag : 시간 방 온도 습도 미세 초미세 Co2 || 에어컨 보일러 제습기 가습기 공기청정기 환풍기 || 화재 기준온도 기준습도


def get_signal():
    from sys import argv
    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()


    
def Calculation (a, Flag):
    print("Room number: ", 101+a)
#    print("flag in Calculation: ", Flag)
    check_1 = 0 #초기화
    print("time signal 101", time_signal[0])
    print("time signal 102", time_signal[1])
    print("signal time table", time_signal[a])

    ###수동제어 체크
    for i in range (0 , 6): 
        if time_signal[a][i][0] != 0:
            check_1 = 1
            break
        else:
            check_1 = 0
    if check_1 == 0: ### 수동제어 없었음->일반 자동신호 시행
        pass
#        print("Auto Control")
#        for i in range (0,6):
#            if Flag[i] == True:
#                #GPIO.output(fan[a], GPIO.HIGH)
#                print("fan on", i)
#            elif Flag[i] == False:
#                #GPIO.output(fan[a], GPIO.LOW)
#                print("fan off ", i)

    elif check_1 == 1:
#        print("Signal Control")
        for i in range (7,13): ### 자동제어 시간체크(자동 제어 시간 계산 및 리스트 완성)
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
#                print("delay: ", delay)
                if delay < 60:
                    if time_signal[a][i][1] == True:
                        #GPIO.output(fan[a], GPIO.HIGH)
                        #print("fan on ", i)
                        Flag[i]=True
                    elif time_signal[a][i][1] == False:
                        Flag[i]=False

                elif delay > 60: 
                    time_signal[a][i] = (0, None)
     
    print("final result: ", Flag)

    udp_send(Flag)
    flag_result = False

    for i in range(7,13):
        if Flag[i]==True:
            GPIO.output(fan[a][i-7], GPIO.HIGH)
            print ("Room", a, "Device ", i-7, "ON")
        else:
            GPIO.output(fan[a][i-7], GPIO.LOW)
            print ("Room", a, "Device ", i-7, "OFF")



def local_sign(): ### 자동 제어 신호 값 처리 및 연산
    while True:
        if ctrl_que.qsize()<=0:
            pass
        else:
            signal_result = ctrl_que.get()
 #           print("signal result: ", signal_result)
            tm = time.time()
            sec = tm%(60*60*24)
    
            if signal_result[0]=="101":
                print("signal: 101")
                for i in range(1,7):
                    if signal_result[i]==True:
                        time_signal[0][i-1] = (sec, True)
                    elif signal_result[i]== False:
                        time_signal[0][i-1] = (sec, False)
                    elif signal_result[i] == None:
                        if time_signal[0][i-1][0]!=0:
                            pass
                        else:
                           time_signal[0][i-1] = (0, None)
                            
            elif signal_result[0]=="102":
                print("signal: 102")
                for i in range(1, 7):
                    if signal_result[i]==True:
                        time_signal[1][i-1] = (sec,True)
                    elif signal_result[i] == False:
                        time_signal[1][i-1] = (sec,False)
                    elif signal_result[i] == None: 
                        if time_signal[1][i-1][0]!=0:
                            pass
                        else:
                            time_signal[1][i-1] = (0, None)
            else:
                pass

        if(flag_que.qsize() <= 0):
            continue
            
        flag = flag_que.get()

        if flag[1] == 101:
            a = 0
            Calculation (a, flag)
        if flag[1] == 102:
            a = 1
            Calculation (a, flag)

        print("========================================================")
        print()
        print()

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
    ble_scan()
    th1.join()
    th2.join()
    th3.join()
    th4.join()

   
    GPIO.output(fan[0], GPIO.LOW)
    GPIO.output(fan[1], GPIO.LOW)
    GPIO.output(fan[2], GPIO.LOW)
