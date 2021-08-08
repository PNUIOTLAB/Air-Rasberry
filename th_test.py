from multiprocessing import Process, JoinableQueue, Queue, Manager
from flask import Flask, request
import json
import time
import sys
import requests

def print1():
   
    while True:
        print("Hi")
        time.sleep(3)

def print2():
    
    while True:
        print("Hello")
        time.sleep(4)

def print3():

    while True:
        print("world")
        time.sleep(5)

app = Flask(__name__)

@app.route('/')
def root():
    return 'welcome to flask'

@app.route('/handle_post', methods=['POST'])
def handle_post():
    params = json.loads(request.get_data(), encoding='utf-8')
    if len(params) == 0:
        return 'No params'

    params_str = ''
    for key in params.keys():
        params_str += 'key: {}, value: {}<br>'.format(key, params[key])
    return params_str


@app.route('/send_post', methods=['GET'])
def send_post():
    params = {
        "param1": "test",
        "param2": 123,
        "param3": "한글"
    }
    res = requests.post("http://127.0.0.1:5000/handle_post", data=json.dumps(params))
    return res.text

if __name__ == '__main__':

    th1 = Process(target=print1)
    th2 = Process(target=print2)
    th3 = Process(target=print3)

    th1.start()
    th2.start()
    th3.start()
    
    app.run(debug=True)

    th1.join()
    th2.join()
    th3.join()
