#Client

import socket

import socket


def GetSocket():
    client = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
   # host = socket.gethostname()
    return client

if __name__ == '__main__':
    while True:
        # addr = client.accept()
        client = GetSocket()
        portnumber = 12333
        addr = (socket.gethostname(),portnumber)
        print("Connection successed")
        while True:  #strip
            msg = raw_input("Online:::input message")
            if(msg == "$"):
                print("Successfully quited\n")
                break
            client.sendto(msg,addr)
            data,addr = client.recvfrom(1024) #
            print('recv:::  ' +  bytes(data) + " ::: From ::: " + bytes(addr)) #
        break