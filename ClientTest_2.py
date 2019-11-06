#Client

import socket

import socket


def GetSocket(portnumber):
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    host = socket.gethostname()
    client.connect((host,portnumber)) #
    return client

if __name__ == '__main__':
    while True:
        # addr = client.accept()

        print("Connection successed")
        while True:  #strip
            client = GetSocket(12333)
            msg = raw_input("Online:::input message")
            if(msg == "$"):
                print("Successfully quited\n")
                break
            client.send(msg)
            data = client.recv(1024)
            client.close()#
            print('recv:::  ' +  bytes(data)) #
        break