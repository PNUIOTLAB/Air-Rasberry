from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import json
from queue import Queue

time = [[],[],[]]
ctrl_que = Queue()
set_que = Queue()
ctrl_result = []
set_result = []

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

        if len(data)<=50:
            setting = json.loads(data)
            set_result = [setting['0'],setting['1']]
            set_que.put(set_result)
            print(set_que.get())
        else:
            ctrl = json.loads(data)
            ctrl_result = [ctrl['0'],ctrl['1'],ctrl['2'],ctrl['3'],ctrl['4'],ctrl['5'],ctrl['6']]
            ctrl_que.put(ctrl_result)
            
            if ctrl_result[6]=='101':
                for i in (0,5):
                    if ctrl_result[i]==True:
                        time[0][i] = True
                    elif ctrl_result[i]==False:
                        time[0][i] = False
                    else:
                        time[0][i] = None
                        
            elif ctrl_result[6]=='102':
                for i in (0,5):
                    if ctrl_result[i]==True:
                        time[0][i] = True
                    elif ctrl_result[i]==False:
                        time[0][i] = False
                    else:
                        time[0][i] = None
                        
            elif ctrl_result[6]=='103':
                for i in (0,5):
                    if ctrl_result[i]==True:
                        time[0][i] = True
                    elif ctrl_result[i]==False:
                        time[0][i] = False
                    else:
                        time[0][i] = None
            else:
                pass

        print(time[0])
        print(time[1])
        print(time[2])
        self._set_response()

def run(server_class=HTTPServer, handler_class=S, port=8080):
    logging.basicConfig(level=logging.INFO)
    server_address = ('192.168.0.49', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')

if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
