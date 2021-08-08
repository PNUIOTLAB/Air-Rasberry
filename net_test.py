from flask import Flask, request
import json
import requests

app = Flask(__name__)

@app.route('/')
def root():
    return 'welcome to flask'

'''
@app.route('/setDevice', methods=['POST']
def set_device():

    print("GET DATA")

    params = json.loads
'''

if __name__ == '__main__':
    app.run(debug=True)
