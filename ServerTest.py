

#Server

import socket
import threading
import time
import select
def getSocket(portnumber):
    serversocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    host = socket.gethostname()
    serversocket.bind((host,portnumber))
    serversocket.setblocking(False)
    serversocket.listen(5)
    return serversocket

def handlereq(conn,addr):
    print("Incoming connection from " + bytes(addr[0]) + " : " + bytes(addr[1]))
    while True:
        try:
            data = conn.recv(1024)
            if (bytes(data) == ''):
                print("Connection from " + bytes(addr[0]) + " : " + bytes(addr[1]) +" has been teared down")
                break
            print("Data Transfering from::" + bytes(addr[0]) + ":::" + bytes(data))
            conn.send("Congrats!" + bytes(addr[0]) + "We have successfully received your message")

        except Exception as e:
            print("Exception happened during data transmitting " + e.message)
            break

    conn.close()

if __name__ == '__main__':
    portnumber = 12333
    serversocket = getSocket(portnumber)
    print("Server Started listening on " + bytes(portnumber) + " at " + socket.gethostname())
    time_started = time.time()
    inputs = [serversocket,]
    while True:
        try:
            r_list, w_list, e_list = select.select(inputs, [], [], 1)
            for event in r_list:
                if event == serversocket:
                    conn,addr = serversocket.accept()
                    inputs.append(conn)
                else:
                    data = event.recv(1024)
                    if data:
                        print("Data Transfering from::" + bytes(data))
                        event.send("Congrats!We have successfully received your message")
                        break
                    else:
                        inputs.remove(event)
                        print("Connection tear down")

        except socket.timeout,e:
            print("socket has timeout")
            exit(1)





