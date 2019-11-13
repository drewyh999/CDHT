import socket
import select

def getSocket(portnumber):
    serversocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    host = socket.gethostname()
    serversocket.bind((host,portnumber))
    serversocket.settimeout(10)
    serversocket.setblocking(False)
    return serversocket

if __name__ == '__main__':
    portnumber = 12333
    server_udp = getSocket(portnumber)
    inputs = [server_udp,]
    print("Listening at" + bytes(portnumber))
    while True:
        r_list, w_list, e_list = select.select(inputs, [], [], 1)
        for event in r_list:
            data, addr = event.recvfrom(1024)
            print("Incoming transmission from" + bytes(addr[0]) + " :::" + bytes(addr[1]) + ":::" + bytes(data))
            server_udp.sendto("Congradulation! UDP Server has received your msg! " + bytes(addr), addr)