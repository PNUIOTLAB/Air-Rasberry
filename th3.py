from multiprocessing import Process, Queue
import time
###import RPi.GPIO as GPIO

###GPIO.setmode(GPIO,BCM)
###GPIO.setwarnings(False)
signal=[0]*7 ###수동제어 신호

time_signal = [[0]*6]*4 ###수동제어 신호시간 모음집

time_local = [0]*6 ###자동 신호 시간 리스트

gigi = [17,27,18,23,24,22] ###기기의 핀 번호
###에어컨,히터,환풍기,가습기,제습기,공기청정기

"""
GPIO.setup(aircon, GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(heater, GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(fan, GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(humidifier, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(dehumidifier, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(aircleaner, GPIO.OUT, initial=GPIO.LOW)"""

def Calculation (a):
    check_1 = 0 #초기화
    ###수동제어 체크
    for i in range (0 , 6):
        if time_signal[a][i] != 0:
            check_1 = 1
            break
        else:
            check_1 = 0

        if check_1 == 0: ### 수동제어 없었음->일반 자동신호 시행
            print("수동제어 없음 일반 자동신호 실행 \n")
            for i in range (0,6):
                if flag[i] == True:
                    ###GPIO.output(gigi[i], GPIO.HIGH)
                    print("gigi on")
                if flag[i] == False:
                    ###GPIO.output(gigi[i], GPIO.LOW)
                    print("gigi off")

        elif check_1 == 1:
            for i in range (0,6): ### 자동제어 시간체크(자동 제어 시간 계산 및 리스트 완성)
                if flag[i] == True:
                    tm= time.time()
                    secs = int(tm % (60*60*24))
                    time_local[i] = secs
                else:
                    time_local[i] = 0
                    
            print("수동제어 감지 값 비교후 시간보다 크면 출력 \n")
            for i in range (0,6): ###수동제어 - 자동제어 시간차 계산
                if time_signal[a][i] > 0:
                    tmp1 = time_signal[a][i]
                    tmp2 = time_local[i]
                    delay = tmp2 - tmp1
                    
                    if delay < 10:
                        print("시간값 못 넘었음 수동제어 신호 ")
                        for i in range (0,6):
                            if signal[i] == True:
                                ###GPIO.output(gigi[i], GPIO.HIGH)
                                print("gigi on")
                            elif signal[i] == False:
                                ###GPIO.output(gigi[i], GPIO.LOW)
                                print("gigi off")

                    elif delay > 10: ### 임의의 시간 보다 클때
                        for i in range (0,6):
                            if flag[i] == True:
                                ###GPIO.output(gigi[i], GPIO.HIGH)
                                print("gigi on")
                            elif flag[i] == False:
                                ###GPIO.output(gigi[i], GPIO.LOW)
                                print("gigi off")
                            time_signal[0][i] = 0 ### 해당하는 시간 초기화
                                                
                    elif time_signal[a][i] == 0:
                        print("시간 값이 없을때 그대로 신호 보내주기\n") 
                        for i in range (0,6):
                            if flag[i] == True:
                                ###GPIO.output(gigi[i], GPIO.HIGH)
                                print("gigi on")
                            elif flag[i] == False:
                                ###GPIO.output(gigi[i], GPIO.LOW)
                                print("gigi off")



def local_sign(): ### 자동 제어 신호 값 처리 및 연산
    flag = [0]*7 ###자동신호
    
    ###queue2 = Queue() 자동신호 큐
    ###flag = queue2.get()
    ### 큐2에서 값 받아오기
    ### queue3 = Queue()
    ### signal = queue3.get()
    ### 큐3에서 값 받아오기

    flag = [False, False, False, False, False,False, 101]  ### 자동신호 제어
    signal = [True, True, False, False, False, False, 102] ###수동신호 제어
    ###1번 방 신호 처리

    if flag[6] == 101:
        a=0
        Calculation (a)
    if flag[6] == 102:
        a=1
        Calculation (a)
    if flag[6] == 103:
        a=2
        Calculation (a)
    if flag[6] == 104:
        a=3
        Calculation (a)

