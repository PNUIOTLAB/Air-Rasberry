from multiprocessing import Process, Queue
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
import logging
import json
import time
import sys

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

ctrl_que = Queue() #수동신호 큐
set_que = Queue()  #임계값 조절 큐
tlqkf_que = Queue() #자동신호 큐

ctrl_result = []    #수동신호 리스트
set_result = []    #임계값 리스트
tlqkf_result = []  #자동신호 리스트

#임계값
Threshold_humidup = [45]
Threshold_humiddown = [35]

Threshold_tempup = [28]
Threshold_tempdown = [22]

Threshold_dust1 = 80
Threshold_dust2 = 35
Threshold_Co2 = 1000

"""
GPIO.setup(aircon, GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(heater, GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(fan, GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(humidifier, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(dehumidifier, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(aircleaner, GPIO.OUT, initial=GPIO.LOW)"""


def tlqkf():
    while(1):
       # flag1 = [True, False, None, None, False, None, 101]
       # flag2 = [None, None, False, True, None, True, 102]
        flag3 = [False, False, True, False, True, False, 103]

       # tlqkf_que.put(flag1)
       # tlqkf_que.put(flag2)
        tlqkf_que.put(flag3)

        time.sleep(1)
        
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
            else:
                pass

            if set_result[1]!=0:
                Threshold_humiup[0] = set_result[1]+5
                Threshold_humidown[0] = set_result[1]-5
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

def run(server_class=HTTPServer, handler_class=S, port=8080):
    logging.basicConfig(level=logging.INFO)
    server_address = ('192.168.0.49', port)
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
    signal = ctrl_que.get()
    tm = time.time()
    sec = int(tm%(60*60*24))
            
    if signal[6]==101:
        print("101")
        for i in range(0,6):
           if signal[i]!=None:
               time_signal[0][i] = sec
           else:
               pass
    elif signal[6]==102:
        print("102")
        for i in range(0,6):
            if signal[i]!=None:
                time_signal[1][i] = sec
            else:
                pass
    elif signal[6]==103:
        print("103")
        for i in range(0,6):
            if signal[i]!=None:
                time_signal[2][i] = sec
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
                print("gigi on")
            if Flag[i] == False:
                ###GPIO.output(gigi[i], GPIO.LOW)
                print("gigi off")

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
            if time_signal[a][i] > 0:
                tmp1 = time_signal[a][i]
                tmp2 = time_local[i]
                delay = tmp2 - tmp1
                    
        if delay < 10:
            print("signal contrl ")
            for i in range (0,6):
                if signal[i] == True:
                    ###GPIO.output(gigi[i], GPIO.HIGH)
                    print("gigi on")
                elif signal[i] == False:
                    ###GPIO.output(gigi[i], GPIO.LOW)
                    print("gigi off")

        elif delay > 10: 
            for i in range (0,6):
                if Flag[i] == True:
                    ###GPIO.output(gigi[i], GPIO.HIGH)
                    print("gigi on")
                elif Flag[i] == False:
                    ###GPIO.output(gigi[i], GPIO.LOW)
                    print("gigi off")
                time_signal[0][i] = 0 
                                                
        elif time_signal[a][i] == 0:
            print("none signal\n") 
            for i in range (0,6):
                if Flag[i] == True:
                    ###GPIO.output(gigi[i], GPIO.HIGH)
                    print("gigi on")
                elif Flag[i] == False:
                    ###GPIO.output(gigi[i], GPIO.LOW)
                    print("gigi off")



def local_sign(): ### 자동 제어 신호 값 처리 및 연산
    
    ###queue2 = Queue() 자동신호 큐
    ###flag = queue2.get()
    ### 큐2에서 값 받아오기
    ### 큐3에서 값 받아오기

#    flag = [True, True, None, None, False,False, 103]  ### 자동신호 제어
    #signal = [True, True, False, False, False, False, 102] ###수동신호 제어
    ###1번 방 신호 처리
    flag = tlqkf_que.get()
    print("get flag: ", flag)
    print("time0: ", time_signal[0])
    print("time1: ", time_signal[1])
    print("time2: ", time_signal[2])
    if flag[6] == 101:
        a=0
        Calculation (a, flag)
    if flag[6] == 102:
        a=1
        Calculation (a, flag)
    if flag[6] == 103:
        a=2
        Calculation (a, flag)
    if flag[6] == 104:
        a=3
        Calculation (a)

if __name__ == '__main__':

    th2 = Process(target=tlqkf)
    th3 = Process(target=local_sign)
    th4 = Process(target=get_signal)

    th2.start()
    th3.start()
    th4.start()

    print("start\n")

    th2.join()
    th3.join()
    th4.join()
