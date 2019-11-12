"""
Test client to Test concurrent webserver

"""

import argparse
import errno
import os
import socket

SERVER_ADDR, PORT = 'localhost', 8888


REQUEST = (
    "GET /hello HTTP/1.1\n"
    + "Host: " + SERVER_ADDR + ":" + str(PORT)
    + "\n\n"
    )

REQUEST = REQUEST.encode()

def main(max_clients, max_connecs):
    sock_list = []

    for client_num in range(max_clients):
        pid = os.fork()

        if(pid == 0):
            for connection_num in range(max_connecs):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((SERVER_ADDR, PORT))
                sock.sendall(REQUEST)
                sock_list.append(sock)
                print(connection_num)
                os._exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description = "Test client for LSBAWS",
        formatter_class = argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--max-connecs",
        type = int,
        default = 1024,
        help = "Maximum number of connections per client."
    )

    parser.add_argument(
        "--max-clients",
        type = int,
        default = 1,
        help = "Maximum number of clients."
    )

    args = parser.parse_args()

    print(args.max_clients, args.max_connecs)
    main(args.max_clients, args.max_connecs)
