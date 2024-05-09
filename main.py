import signal
import socket
import threading


class ProxyServer:
    def _init_(self, config):
        # Shutdown on Ctrl+C
        signal.signal(signal.SIGINT, self.shutdown)

        # Create a TCP socket
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Re-use the socket
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # bind the socket to a public host, and a port
        self.serverSocket.bind((config['HOST_NAME'], config['BIND_PORT']))

        self.serverSocket.listen(10)  # become a server socket
        self.__clients = {}

        while True:
            # Establish the connection
            (clientSocket, client_address) = self.serverSocket.accept()

            d = threading.Thread(name=self._getClientName(client_address),
                                 target=self.proxy_thread, args=(clientSocket, client_address))
            d.setDaemon(True)
            d.start()

    def proxy_thread(self, conn, client_address):
        # get the request from browser
        request = conn.recv(config['MAX_REQUEST_LEN'])

        # parse the first line
        first_line = request.split(b'\n')[0]

        # get url
        url = first_line.split(b' ')[1]

        http_pos = url.find(b"://")  # find pos of ://
        if (http_pos == -1):
            temp = url
        else:
            temp = url[(http_pos + 3):]  # get the rest of url

        port_pos = temp.find(b":")  # find the port pos (if any)

        # find end of web server
        webserver_pos = temp.find(b"/")
        if webserver_pos == -1:
            webserver_pos = len(temp)

        webserver = ""
        port = -1
        if (port_pos == -1 or webserver_pos < port_pos):
            # default port
            port = 80
            webserver = temp[:webserver_pos]
        else:  # specific port
            port = int((temp[(port_pos + 1):])[:webserver_pos - port_pos - 1])
            webserver = temp[:port_pos]

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(config['CONNECTION_TIMEOUT'])
        s.connect((webserver, port))
        s.sendall(request)

        while True:
            # receive data from web server
            data = s.recv(config['MAX_REQUEST_LEN'])

            if (len(data) > 0):
                conn.send(data)  # send to browser/client
            else:
                break

    def _getClientName(self, client_address):
        return "Client_Thread_" + client_address[0] + "_" + str(client_address[1])

    def shutdown(self, signum, frame):
        self.serverSocket.close()
        exit()


# Example configuration
config = {
    'HOST_NAME': '127.0.0.1',
    'BIND_PORT': 8888,
    'MAX_REQUEST_LEN': 4096,
    'CONNECTION_TIMEOUT': 5
}

if _name_ == "_main_":
    proxy_server = ProxyServer(config)