"""
Concurrent Python Webserver than can be used by all python webframeworks
Uses Python Web Server to interact with all frameworks
"""

import io
import socket
import sys
import datetime
import errno
import signal
import os

DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
    ]

MONTHS = [
    "None",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

def reaper(sig_num, frame):
    #kill zombie children after completion
    while True:
        try:
            #wait for child process but don't block
            pid, status = os.waitpid(-1, os.WNOHANG)

        except OSError:
            return

        if pid == 0:
            #all zombies killed
            return

def parse_server_time(today_obj):
    # ('Date', 'Sat, 9 Nov 2019 1:12:23 GMT'),
    ret_str = (
            DAYS[today_obj.weekday()][:3] + ", "
            + str(today_obj.day) + " "
            + MONTHS[today_obj.month][:3] + " "
            + str(today_obj.year) + " "
            + str(today_obj.hour) + ":"
            + str(today_obj.minute) + ":"
            + str(today_obj.second) + " "
            + "GMT"
        )

    # print(ret_str)
    return ret_str

class WSGIServer(object):
    addr_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    request_queue_size = 1024

    def __init__(self, server_addr):
        #create socket
        self.listen_socket = listen_socket = socket.socket(
            self.addr_family,
            self.socket_type
        )

        #allow us to reuse the same addr for multiple connections and listen on socket
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen_socket.bind(server_addr)
        listen_socket.listen(self.request_queue_size)

        host, port = self.listen_socket.getsockname()[:2]
        # print(self.listen_socket.getsockname())
        self.server_name = socket.getfqdn(host)
        self.server_port = port

        self.headers_set = []

    def set_app(self, application):
        self.application = application

    def serve_forever(self):
        listen_socket = self.listen_socket

        #reap child zombie process
        signal.signal(signal.SIGCHLD, reaper)

        while True:
            try:
                #accept new client connetions and handle each request
                self.client_connection, client_address = listen_socket.accept()

            except IOError as e:
                code, msg = e.args

                #incase of signal interrupt during system call
                if code == errno.EINTR:
                    continue
                else:
                    raise

            #start child
            pid = os.fork()

            if pid == 0:
                #in child
                listen_socket.close()
                self.handle_one_request()
                self.client_connection.close()
                os._exit(0)
            else:
                #in parent
                self.client_connection.close()

    def handle_one_request(self):
        #recv data from socket and parse
        request_data = self.client_connection.recv(1024)

        self.request_data = request_data = request_data.decode('utf-8')

        print(''.join(f'< {line}\n' for line in request_data.splitlines()))

        self.parse_request(request_data)

        #construct env
        env = self.get_environ()

        #start appication and return HTTP response
        result = self.application(env, self.start_response)
        self.finish_response(result)

    def parse_request(self, text):
        request_line = text.splitlines()[0]
        request_line = request_line.rstrip('\r\n')

        #get components from request line
        self.request_method, self.path, self.request_ver = request_line.split()

    def get_environ(self):
        env  = {
            'wsgi.version' : (1, 0),
            'wsgi.url_scheme' : 'http',
            'wsgi.input' : io.StringIO(self.request_data),
            'wsgi.errors' : sys.stderr,
            'wsgi.multithread' : False,
            'wsgi.multiprocess' : False,
            'wsgi.run_once' : False,
            'REQUEST_METHOD' : self.request_method,
            'PATH_INFO' : self.path,
            'SERVER_NAME' : self.server_name,
            'SERVER_PORT' : str(self.server_port),
        }

        return env

    #required by wsgi specs
    def start_response(self, status, response_headers, exc_info=None):
        today = datetime.datetime.today()
        server_date = parse_server_time(today)
        #add necessary server headers
        server_headers = [
            ('Date', server_date),
            ('Server', 'WSGIServer 0.2')
        ]

        self.headers_set = [status, response_headers + server_headers]

    def finish_response(self, result):
        try:
            status, response_headers = self.headers_set
            response = f'HTTP/1.1 {status}\r\n'
            for header in response_headers:
                # print(header)
                response += '{0} : {1}\r\n'.format(*header)

            response += '\r\n'

            for data in result:
                response += data.decode('utf-8')

            print(''.join(f'> {line}\n' for line in response.splitlines()))

            response_bytes = response.encode()
            self.client_connection.sendall(response_bytes)
        finally:
            self.client_connection.close()


SERVER_ADDR = (HOST, PORT) = '', 8888

def make_server(server_addr, application):
    server = WSGIServer(server_addr)
    server.set_app(application)
    return server


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('Provide a WSGI application object as module:callable')
    app_path = sys.argv[1]
    module, application = app_path.split(':')
    module = __import__(module)
    application = getattr(module, application)
    httpd = make_server(SERVER_ADDR, application)
    print(f'WSGIServer: Serving HTTP on port {PORT} ...\n')
    httpd.serve_forever()
