

#Server

import socket
import threading
import time

def getSocket(portnumber):
    serversocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    host = socket.gethostname()
    serversocket.bind((host,portnumber))
    #serversocket.settimeout(20)
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
    while True:
        try:
            if time.time() - time_started < 5:
                conn, addr = serversocket.accept()
                threading.Thread(target=handlereq,args=(conn,addr)).start()
            else:
                print("timeout")
                serversocket.close()
                break
        except socket.timeout,e:
            print("socket has timeout")
            exit(1)





