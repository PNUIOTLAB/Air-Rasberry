from multiprocessing import Process, JoinableQueue, Queue, Manager
from http.server import BaseHTTPRequestHandler, HTTPServer
from bluepy.btle import Scanner, DefaultDelegate
from flask import Flask, request
import json
import time
import sys
import requests
import RPi.GPIO as GPIO


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

std_temp = [25, 25]

std_dust1 = 200
std_dust2 = 200
std_Co2 = 6000

Target_device_addr = ["20:20:1d:27:d1:17", "ac:1a:30:f0:49:8c"]


GPIO.setup(device[0][0], GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(device[0][1], GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(device[0][5], GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(device[1][2], GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(device[1][3], GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(device[1][4], GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(13, GPIO.OUT, initial = GPIO.LOW)

app = Flask(__name__)


class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)
    '''
    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            print("Discovered device", dev.addr)
        elif isNewData:
            print("Recieved new data from", dev.addr)
    '''

def ble_scan():
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
                        if dev.addr == "ac:1a:30:f0:49:8c":
                           data_tmp[6] = 101
                        elif dev.addr == "20:20:1d:27:d1:17":
                           data_tmp[6] = 102
                        print (data_tmp)
                        data_que.put(data_tmp)


@app.route('/setDevice', methods=['POST']) # 사용자 수동 제어 수신
def set_device():
    print("GET Control  DATA")
    params = json.loads(request.get_data(), encoding='utf-8') # json 타입으로 데이터 수신
    
    if len(params) == 0:
        return "No params"
            
    else: 
        set_ctrl = [params['Room'],params['AC'],params['Boiler'],params['Dehumidifier'], # 기기별 제어 신호 
                    params['Humidifier'],params['Aircleaner'],params['Fan']]

        print("control siganl: ", ctrl_result)

        ctrl_que.put(set_result)
    
    print("CONTROL FINISH")    

@app.route('/setEnvir', methods=['POST']) # 사용자 온습도 설정 수신
def set_envir():
    
    print("GET SETTING DATA")
    params = json.loads(request.get_data(), encoding='utf-8') # json 타입으로 데이터 수신
    
    if len(params) == 0:
        return "No params"

    
    else: 
        set_result = [params['Room'],params['set_humid'],params['set_temp']]

        if set_result[1]!=0:
                thres_que.put((set_result[0], set_result[1], "humid"))

        elif set_result[2]!=0:
                thres_que.put((set_result[0], set_result[2], "temp"))
    print("SET FINISH")

def make_flag(): 

    oldtemp = 25
    r = 0
    
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
                 
        if (data_que.qsize() <= 0):
            continue
        
        (temp, humid, micro_dust, dust, gas, time, room)=data_que.get()

        if room == '101':
            r = 0
        elif room == '102':
            r = 1

        print("room: ", r)
        
        if(temp > std_temp[r]+1): 
            Flag[7]=True
        elif(temp < std_temp[r]-1):
            Flag[8]=True

        if(humid > std_humid[r]+10):
            Flag[9]=True
        elif(humid < std_humid[r]-10):
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
        Flag[14] = std_temp[r]
        Flag[15] = std_humid[r]
        print("Flag : ",Flag)
        
# Flag : 시간 방 온도 습도 미세 초미세 Co2 || 에어컨 보일러 제습기 가습기 공기청정기 환풍기 || 화재 기준온도 기준습도
        flag_que.put(Flag)


@app.route('/send_post', methods=['GET'])
def send_post():

    if (send_que.qsize() <= 0):
        return "No params"

    send_result = send_que.get()

    print("data for send: ", send_result)

    params = {
            "Time": send_result[0],
            "Room": send_result[1],
            "Temp": send_result[2],
            "Humid": send_result[3],
            "PM25": send_result[4],
            "PM10": send_result[5],
            "Co2": send_result[6],
            "AC": send_result[7],
            "Boiler": send_result[8],
            "Dehumidifier": send_result[9],
            "Humidifier": send_result[10],
            "AirCleaner": send_result[11],
            "Fan": send_result[12],
            "Fire": send_result[13],
            "StandTemp": send_result[14],
            "StandHumid": send_result[15]
        }
    
    res = requests.post("http://192.168.0.27:9000/ENVIRdata", data=json.dumps(params))

    return res.text



def Calculation (a, Flag):
    print("Room number: ", 101+a)
#    print("flag in Calculation: ", Flag)
    check_1 = 0 #초기화
    print("time signal 101", time_signal[0])
    print("time signal 102", time_signal[1])
    print("signal time table", time_signal[a])

    ###수동제어 체크
    for i in range (0, 6): 
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
                        Flag[i+7] = True
                    elif time_signal[a][i][1] == False:
                        Flag[i+7] = False

                elif delay > 60: 
                    time_signal[a][i] = (0, None)

    print("final result: ", Flag)
    send_que.put(Flag)


    for i in range(7,13):
        if Flag[i] == True:
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
            
            if signal_result[0] == '101':
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
                           
            elif signal_result[0] == '102':
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

        if flag[6] == 101:
            a=0
            Calculation (a, flag)
        if flag[6] == 102:
            a=1
            Calculation (a, flag)

        print("========================================================")
        print()
        print()
        print()


if __name__ == '__main__':

    GPIO.output(device[0], GPIO.LOW)
    GPIO.output(device[1], GPIO.LOW)

    
    th1 = Process(target=ble_scan)
    th2 = Process(target=make_flag)
    th3 = Process(target=local_sign)
    

    th1.start()
    th2.start()
    th3.start()

    app.run(debug=True)

#    th1.join()
#    th2.join()
#    th3.join()
   
    






        

    

                         










                    
