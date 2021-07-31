#_*_coding: utf-8_*_

from flask import Flask, request
import json
import requests
import time

app = Flask(__name__)

@app.route('/')
def route():
    return 'welcome to flask'

@app.route('/handle_post', methods=['POST'])
def handle_post():
    params = json.loads(request.get_data(), encoding='utf-8')
    if len(params) == 0:
        return 'No Params'

    params_str = ''
    for key in params.keys():
        params_str += 'key: {}, value: {}<br>'.format(key, params[key])
    return params_str

@app.route('/send_post', methods=['GET'])
def send_post():
    now = time.strftime('%y-%m-%d %H:%M:%S')
    params = {
        "Time": now,
        "Room": '101',
        "Temperature": 25.00,
        "Humidity": 50.00,
        "PM25": 20,
        "PM10": 23,
        "Co2": 2400.00,
        "AC": True,
        "Heater": False,
        "Dehumidifier": True,
        "Humidifier": False,
        "Aircleaner": True,
        "Fan": False
    }
    res = requests.post("http://127.0.0.1:5000/handle_post", data=json.dumps(params))
    return res.text
        

if __name__ == '__main__':
    app.debug = True
    app.run()


