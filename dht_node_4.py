'''     1.Every node is immediatly aware of its successor and the successor's successor
        2.When entering the network, a newly joined node need to specify those two nodes above
        3.Predecessors are awared via ping requests from them
        4.Global variables for peers: sucnode_1, sucnode_2, prenode_1,
        5.One UDP listener for pinging sending and receiving
        6.Short cuts var for storing the short cut
        7.One TCP listener for file transmission and request and storing
        8.Command Line params: sucnode_1 prenode (with UDP port number)
'''
import sys
import threading
import socket
import time
import select
import os
import datetime

UDP_PORT_BASE = 30000;#port base for udp transmission
TCP_PORT_BASE = 50000;#port base for tcp transmission
FILE_PORT_BASE = 60000;#port base for file transmission
HAVE_SUCNODE2 = False;#currently got the sucnode_2
PRENODE_INFORMED = False #inform the prenode to change the sucnode_1
STATUS_PING_TIMEOUT = 5.0; #timeout that a ping to test alive
BUFFER = 1024;
SHOW_TRIVAL_MSG = False;#show the ping message or not
SHORTCUT_AVA = False;#the shortcut node is alive or not
SUCNODE1_AVA = False;#the sucnode_1 is alive or not
STATUS_PING_INTERVAL = 3.0;
NODE_TIMEOUT_INTERVAL = 5.0;#the maximum time a node have to respond to a ping req
MAX_TCP_CONN = 5; #Max TCP connection that could be handled at the same time
MAX_ID = 255;#Max number of peer#TODO limit the id number
FILE_ALLOCATED_TO_SELF = 5
FILE_NOT_ALLOCATED_TO_SELF = 8
TRAN = 1 #Mode for file transmission, give the file to the destination
DOWNLOAD = 0 #Mode for file download get the file from destination
SHORTCUT_NUMBER = 0
SEND_SCT_ACK = False
LOCALHOST = socket.gethostbyname(socket.gethostname())


def initialization():
    if len(sys.argv) - 1 < 2:
        print("usage: [self_identifier] [successor node(IP:port#)] [predecessor node(IP:port#)]")
        #print("This application is meant to implement a ")
        exit(1)

    global sucnode_1, sucnode_2,prenode,shortcutnode,self_identifier,pre_id,suc_id,SUCNODE1_AVA
    try:
        #Get self_identifier by directly have the port number decrease by UDP port base
        #If the sucnode is not specified just add the prenode's ID to 10 and make it own
        sucnode_1 = None
        sucnode_2 = None
        prenode = None
        if sys.argv[2] == "null" and sys.argv[1] == "null":
            SUCNODE1_AVA = False
            self_identifier = 1
        elif sys.argv[1] == "null":
            SUCNODE1_AVA = False
            prenode = ((sys.argv[2].split(":")[0]), int((sys.argv[2].split(":")[1])))
            pre_id = prenode[1] - UDP_PORT_BASE
            self_identifier = pre_id + 120

        #If it is the first node than we assign 1 to selfID

        #If we have both suc and pre node ,than just calculate the avg of their ID as own ID
        else:
            sucnode_1 = ((sys.argv[1].split(":")[0]), int((sys.argv[1].split(":")[1])))
            prenode = ((sys.argv[2].split(":")[0]), int((sys.argv[2].split(":")[1])))
            pre_id = prenode[1] - UDP_PORT_BASE
            suc_id = sucnode_1[1] - UDP_PORT_BASE
            self_identifier = (pre_id + suc_id) / 2

    except Exception as e:
        print("Input strings seems to be unable to parse\n" + e.message)
        exit(1)
    main_procedure()


def UrgentContact():
    global sucnode_1,HAVE_SUCNODE2,SUCNODE1_AVA,last_suc_reply,suc_id
    if not HAVE_SUCNODE2:
        print("Unforunately We Don't have the successor node 2")
        return
    urgent_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    urgent_socket.settimeout(STATUS_PING_TIMEOUT)
    urgent_socket.sendto("SEQ", sucnode_2)
    u_data, u_addr = urgent_socket.recvfrom(BUFFER)
    if u_data == "ACK" and u_addr == sucnode_2[1]:
        sucnode_1 = sucnode_2
        suc_id = sucnode_1[1] - UDP_PORT_BASE
        HAVE_SUCNODE2 = False
        last_suc_reply = time.time()
        SUCNODE1_AVA = True
        print("Fortunately Successor node 2 is Online! Setting successor node 1 to him!")
    else:
        SUCNODE1_AVA = False
        HAVE_SUCNODE2 = False

def printbycom(str,show_trival_msg):
    if(show_trival_msg):
        print(str)
    else:
        return

def myhash(target):
    SUM = 0
    for i in target:
        SUM += ord(i)
    return (SUM * 5) % MAX_ID

def Contact_and_Transfer(src_ip,src_port,mode,filename):
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sock.connect((src_ip,src_port))
    # if self had been requested to transfer a file allocated to self, then we
    # firstly scan the directory the whether we have that file, than if we have it,
    # Transmit the command with the beginning of "FILE_READY" otherwise we say "FILE_NOT_AVA"
    if mode == TRAN:
        fpath = "localdata/" + filename
        if os.path.isfile(fpath):
            # Send Ready and transmit
            sock.send("FILE_READY")
            printbycom("We have the file they want! sending back confirmation",SHOW_TRIVAL_MSG)
            response = sock.recv(BUFFER)
            if response == "RECV_READY":
                fo = open(fpath, 'rb')
                assert fo
                while True:
                    filedata = fo.read(1024)
                    if not filedata:
                        break
                    sock.send(filedata)
                fo.close()
            sock.close()
            printbycom("Transmision completed!",SHOW_TRIVAL_MSG)
        else:
            printbycom("We do not have the file here in local data maybe there is an error",SHOW_TRIVAL_MSG)
            sock.send("FILE_NOT_AVA")
            sock.close()

    # if we are supposed to store the file ,just simply tell the source we are ready and receive
    # the file
    else:
        printbycom("We are supposed to store the file,waiting on receiveing......",SHOW_TRIVAL_MSG)
        sock.send("RECV_READY")
        fpath = "localdata/"  + filename
        fo = open(fpath,'wb')
        while True:
            recvdata = sock.recv(BUFFER)
            if not recvdata:
                break
            fo.write(recvdata)
        printbycom("Successfully received file from" + bytes(src_ip) + ":" + bytes(src_port),SHOW_TRIVAL_MSG)
        sock.close()


#TODO Save the file or Transmit the file properly according to the "mode"

def Send_TCP_msg(msg,ip,port):
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sock.connect((ip,int(port)))
    sock.send(msg)
    sock.close()
def Send_UDP_msg(msg,ip,port):
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.sendto(msg,(ip,port))
    sock.close()


def Status_monitor():
    '''
    // 1.Ping the sucnode_1 only, if it is surely dead, ping sucnode_2, then if sucnode_2 is dead too,
        ask the user to specify a new successor
    '''
    global sucnode_1,sucnode_2,prenode,shortcutnode,self_identifier,pre_id,suc_id
    global SUCNODE1_AVA,SHORTCUT_AVA,HAVE_SUCNODE2
    global SEND_SCT_ACK,shortcutpre

    global last_suc_reply
    last_suc_reply = time.time()#the time last suc ack arrived
    last_suc_sent = 0 #the time that last ping to sucnode_1 was sent
    global last_sct_reply#Set to time() when need shortcut so that they won't be judged as timeout in the first round
    last_sct_sent = 0

    udp_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    udp_socket.setblocking(False)
    udp_socket.bind((socket.gethostname(),UDP_PORT_BASE + self_identifier))

    inputs = [udp_socket, ]
    outputs = [udp_socket,]
    while True:
        try:
            data = None
            addr = None
            r_list, w_list, e_list = select.select(inputs, outputs, [], 1)
            for event in r_list:
                    try:
                        data,addr = event.recvfrom(BUFFER)
                        ip = addr[0]
                        port = addr[1]
                        msg_type = data
                        if msg_type == "SEQ":
                            # handle incoming ping request by send back ack
                            printbycom("Incomming ping message from" + bytes(addr), SHOW_TRIVAL_MSG)
                            # Set the prenode to the node that is pingping current node
                            prenode = addr
                            pre_id = prenode[1] - UDP_PORT_BASE
                            udp_socket.sendto("ACK", (ip, port))
                        if msg_type == "ACK" and addr == sucnode_1:
                            last_suc_reply = time.time()
                            printbycom("Successor node " + bytes(sucnode_1) + " is online", SHOW_TRIVAL_MSG)

                        if msg_type == "SCTACK":
                            SHORTCUT_AVA = True
                            shortcutnode = addr
                            last_sct_reply = time.time()
                            printbycom("Short cut node " + bytes(shortcutnode) + " is online", SHOW_TRIVAL_MSG)

                        if msg_type == "SCTSEQ":
                            udp_socket.sendto("SCTACK", (ip, port))
                            printbycom("We have become a short cut node for" + bytes(addr), SHOW_TRIVAL_MSG)
                        break
                    except Exception as e:
                        print("Exception happens among socket receiving" + e.message)
            for w_events in w_list:
                if SEND_SCT_ACK:
                    w_events.sendto("SCTACK",shortcutpre)
                    SEND_SCT_ACK =False

            if SUCNODE1_AVA and (time.time() - last_suc_sent > STATUS_PING_INTERVAL):
                last_suc_sent = time.time()
                udp_socket.sendto("SEQ", sucnode_1)
                printbycom("Sending ping to test " + bytes(sucnode_1),SHOW_TRIVAL_MSG)

            if SUCNODE1_AVA and (time.time() - last_suc_reply > NODE_TIMEOUT_INTERVAL):#if the sucnode is timeout ,try to contact sucnode_2
                print("Successor node 1 is proved to be offline, trying to contact successor node 2")
                SUCNODE1_AVA = False
                #TODO need a restriction in port use when using multithreading ?
                thread = threading.Thread(target=UrgentContact)
                thread.setDaemon(True)
                thread.start()

            if SHORTCUT_AVA and (time.time() - last_sct_sent > STATUS_PING_INTERVAL):
                last_sct_sent = time.time()
                udp_socket.sendto("SCTSEQ", shortcutnode)
                printbycom("Sending ping to test Short cut" + bytes(shortcutnode), SHOW_TRIVAL_MSG)

            if SHORTCUT_AVA and (time.time() - last_sct_reply > NODE_TIMEOUT_INTERVAL):  # if the sucnode is timeout try to contact sucnode_2
                SHORTCUT_AVA = False
                Send_TCP_msg("SCT:" + bytes(SHORTCUT_NUMBER) + ":" + bytes(
                    LOCALHOST) + ":" + bytes(
                        UDP_PORT_BASE + self_identifier), sucnode_1[0], suc_id + TCP_PORT_BASE)
                printbycom("Short cut node 1 is proved to be offline We are trying to find a new one",SHOW_TRIVAL_MSG)

        except socket.timeout as e:
            print("Socket timout")
        except Exception as e:
            print("Exception happened during udp ping receiving" + e.message)
            continue


def Command_monitor():

    global last_sct_reply, last_suc_reply, sucnode_1,self_identifier,HAVE_SUCNODE2,SUCNODE1_AVA,sucnode_2,suc_id
    global JOINING_NETWORK
    global SEND_SCT_ACK,shortcutpre
    tcp_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    tcp_sock.bind((socket.gethostname(),TCP_PORT_BASE + self_identifier))
    tcp_sock.setblocking(False)
    tcp_sock.listen(MAX_TCP_CONN)

    inputs = [tcp_sock, ]
    while True:
        #TCP monitor need to be none blocking
        #command as the first string before ':'
        while True:
            r_list, w_list, e_list = select.select(inputs, [], [], 1)
            for event in r_list:
                if event == tcp_sock:
                    new_sock, addr = event.accept()
                    inputs.append(new_sock)
                else:
                    data = event.recv(BUFFER)
                    command = bytes(data).split(":")[0]
                    if data:
                        if command == "QUIT":
                            print("Our successor node " + bytes(sucnode_1) + "is leaving the network")
                            # if we do not have a suc_node 2, just let the user to specify a new successor
                            if not HAVE_SUCNODE2:
                                SUCNODE1_AVA = False
                                print("Sucnode has quit and we do not have the sucnode 2", SHOW_TRIVAL_MSG)
                            # if we do have a sucnode 2, make it the sucnode_1 and update the suc_id
                            else:
                                HAVE_SUCNODE2 = False
                                sucnode_1 = sucnode_2
                                suc_id = sucnode_1[1] - UDP_PORT_BASE
                                print("Now " + bytes(sucnode_1) + "is my successor node")
                            break

                        # Handling the new node joining the network
                        # Set the sucnode via the info and set have sucnode2 to false to find a new backupnode
                        if command == "JOIN":
                            ip = data.split(":")[1]
                            port = int(data.split(":")[2])
                            sucnode_1 = (ip,port)
                            suc_id = sucnode_1[1] - UDP_PORT_BASE
                            HAVE_SUCNODE2 = False
                            print("A new Node" + bytes(sucnode_1) + " has joined the network")
                        # Handling the new predecessor's request to ask for next node
                        if command == "ASKNEXT":
                            # Tell the pre node
                            if SUCNODE1_AVA:
                                event.send("NEXT:" + bytes(sucnode_1[0]) + ":" + bytes(sucnode_1[1]))
                                printbycom("PreNode " + bytes(addr[0]) + ":" + bytes(addr[1]) + "is asking for next node",
                                       SHOW_TRIVAL_MSG)
                            else:
                                event.send("NEXT:NULL")
                            break
                        # Handling the File storing request, if we are supposed to store the file, than store it
                        # Else we transmit it to next node
                        if command == "STORE" or command == "REQ":
                            # Compare the myhash value with the self ID and suc_node ID
                            filename = data.split(":")[1]
                            src_ip = data.split(":")[2]
                            src_port = int(data.split(":")[3])

                            printbycom("Node" + bytes(addr[0]) + ":" + bytes(
                                addr[1]) + "is" + command.lower() + "for" + filename, SHOW_TRIVAL_MSG)
                            if Check_File_Ava(filename) == FILE_ALLOCATED_TO_SELF:
                                printbycom("File is avaliable here", SHOW_TRIVAL_MSG)
                                # TODO Maybe multi threading is better?  We may need a variable to restrict the maximum threads within a single node
                                if command == "REQ":
                                    Contact_and_Transfer(src_ip, src_port, TRAN,filename)
                                else:
                                    Contact_and_Transfer(src_ip, src_port, DOWNLOAD,filename)
                                break
                            # If the myhash value is greater than both self and the successor node ID we forward the command
                            elif Check_File_Ava(filename) == FILE_NOT_ALLOCATED_TO_SELF:
                                # If the successor node is ava than forward the message
                                if SUCNODE1_AVA:
                                    printbycom("File is not ava here ,forwarding the request", SHOW_TRIVAL_MSG)
                                    Send_TCP_msg(command, sucnode_1[0], suc_id + TCP_PORT_BASE)
                                    break
                        # Handle shortcut searching request
                        if command == "SCT":
                            searchcount = int(data.split(":")[1])
                            src_ip = data.split(":")[2]
                            src_port = int(data.split(":")[3])
                            printbycom("Incomming SCT request from" + bytes(addr) +
                                       "with the message from " + bytes(src_ip) + bytes(src_port), SHOW_TRIVAL_MSG)
                            # If the search count is down to 1 than we know that self is the shortcut node
                            # that the node is looking for
                            if searchcount == 1:
                                printbycom("Shortcut searching hit! Responding back", SHOW_TRIVAL_MSG)


                                # Just send the SCTACK to the dest ip and port to notify him we are the
                                # short cut node his looking for

                                shortcutpre = (src_ip,src_port)
                                SEND_SCT_ACK = True
                            else:
                                # Else we just decrease the search count by 1 and forward the request
                                searchcount = searchcount - 1
                                if SUCNODE1_AVA:
                                    Send_TCP_msg("SCT:" + bytes(searchcount) + ":" + bytes(src_ip) + ":" + bytes(src_port),sucnode_1[0], suc_id + TCP_PORT_BASE)
                        break
                    else:
                        inputs.remove(event)
            #After the iteration we send out a message to ask for sucnode2 if we do not have one
            if SUCNODE1_AVA and not HAVE_SUCNODE2:
                Get_nextnode(sucnode_1[0], suc_id + TCP_PORT_BASE)


def Check_File_Ava(filename):
    myhashvalue = myhash(filename)

    if myhashvalue == self_identifier:
        return FILE_ALLOCATED_TO_SELF

    #If we are at the end of the circle just allocate to self
    elif self_identifier > suc_id:
        return FILE_ALLOCATED_TO_SELF

    # If One of self and the predecessor node is meant to store the file, than just store it cause we have compared in the cases below
    elif self_identifier > myhashvalue > pre_id:
        return FILE_ALLOCATED_TO_SELF

    elif self_identifier < myhashvalue < suc_id:
        # If One of self and the successor node is meant to store the file, than compare which one is closer
        if abs(myhashvalue - self_identifier) < abs(myhashvalue - suc_id):
            return FILE_ALLOCATED_TO_SELF
        else:
            return FILE_NOT_ALLOCATED_TO_SELF
    #Just return not allocated to self otherwise
    else:
        return FILE_NOT_ALLOCATED_TO_SELF

def Get_nextnode(ip,port):
    addr = (ip,port)
    global HAVE_SUCNODE2,sucnode_2
    try:
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock.connect(addr)
        sock.send("ASKNEXT")
        printbycom("Sending out request to ask for sucnode 2",SHOW_TRIVAL_MSG)
        data = sock.recv(BUFFER)
        if data:
            if data.split(":")[1] != "NULL":
                HAVE_SUCNODE2 = True
                sucnode_2 = (data.split(":")[1],int(data.split(":")[2]))
                sock.close()
            else:
                printbycom("It seems our succseeor node does not have successor",SHOW_TRIVAL_MSG)
                HAVE_SUCNODE2 = False
                sock.close()
    except Exception as e:
        print("Exception happens during getting the next node " + e.message)


def main_procedure():
    global sucnode_1, sucnode_2,prenode,shortcutnode,self_identifier,pre_id,suc_id,SUCNODE1_AVA
    global SHORTCUT_NUMBER,HAVE_SUCNODE2,SHOW_TRIVAL_MSG,last_suc_reply,last_sct_reply
    global JOINING_NETWORK
    if sucnode_1 != None and prenode != None:
        print("Attempting to joining the network with successor " + sucnode_1[0] + " and the predecessor " + prenode[0])
        try:
            Send_TCP_msg("JOIN:" + bytes(LOCALHOST) + ":" + bytes(UDP_PORT_BASE + self_identifier),prenode[0],pre_id + TCP_PORT_BASE)
            SUCNODE1_AVA = True
        except Exception as e:
            print("Exception happens when trying to join the network " + e.message)
            sys.exit(1)


    # TODO Change the global last_sct_reply to time.time() when the shortcut is needed
    # TODO Change the last_suc_reply to time.time() when specifying new successor
    #TODO If we do not have the suc_node specified in the first place or we do not have the pre node info
    # We directly add the pre node ID to 50 as the self ID in the first case and we assign the ID 1 to self
    # Use 1 as the ID in the second case
    #TODO how to setup shortcut
    #TODO How will the file requests be performed when shortcut is needed
    #File Storing and Requesting Command Format 'STORE:[filename]:[localhost_name]:[localhost_port]'
    #Shortcut searching command format 'SCT:[localhost_name]:[localhost_name]:[search_count]'
    #Joining the network
    thread_1 = threading.Thread(target=Status_monitor)
    thread_1.setDaemon(True)
    thread_1.start()
    thread_2 = threading.Thread(target=Command_monitor)
    thread_2.setDaemon(True)
    thread_2.start()

    #variable to store the shortcut count we need

    while True:

        if not SUCNODE1_AVA:
            try:
                print("It seems our sucessor node is now not available please specify a new one")
                str = raw_input("input the suc_node ip and UDP port number divided by ':'")
                sucnode_1  = (str.split(":")[0], int(str.split(":")[1]))
                suc_id = sucnode_1[1] - UDP_PORT_BASE
                SUCNODE1_AVA = True
                HAVE_SUCNODE2 = False
                last_suc_reply = time.time()
                continue
            except Exception as e:
                print("exception happened when parsing the address please retry")
                continue

        command = raw_input("Please input next command")
        if command == "exit":
            try:
                Send_TCP_msg("QUIT", prenode[0], pre_id + TCP_PORT_BASE)
                print("successfully quited the network")
                sys.exit(1)
            except Exception as e:
                print("Exception happened when quiting the network")
        elif command.split(" ")[0] == "set":
            param = command.split(" ")[1]
            if param == "shortcut":
                SHORTCUT_NUMBER = int(command.split(" ")[2])
                Send_TCP_msg("SCT:" + bytes(SHORTCUT_NUMBER) + ":" + bytes(LOCALHOST) + ":" + bytes(
                    UDP_PORT_BASE + self_identifier), sucnode_1[0], suc_id + TCP_PORT_BASE)
                continue
            elif param == "sucnode":
                try:
                    HAVE_SUCNODE2 = False
                    sucnode_1 = (command.split(" ")[2].split(":")[0],int (command.split(" ")[2].split(":")[1]))
                    last_suc_reply = time.time()
                    continue
                except Exception as e:
                    print("Exception happens during parsing" + e.message)
                    continue
            elif param == "showpingmsg":
                switch = command.split(" ")[2]
                if switch == "on":
                    SHOW_TRIVAL_MSG = True
                    print("Now the ping message should be seen")
                else :
                    SHOW_TRIVAL_MSG = False
                    print("Now the ping message is not visible")
        elif command.split(" ")[0] == "get":
            param = command.split(" ")[1]
            if param == "self_udp_port":
                print("UDP port:" + bytes(UDP_PORT_BASE + self_identifier))
                continue
            elif param == "self_tcp_port":
                print("TCP port:" + bytes(TCP_PORT_BASE + self_identifier))
                continue
            elif param == "prenode":
                print("prenode is:" + bytes(prenode))
            elif param == "sucnode":
                print("sucnode is:" + bytes(sucnode_1))
            elif param == "backupnode":
                str = bytes(sucnode_2) if HAVE_SUCNODE2 else "no backup node avaliable"
                print("backupnode is:" + str)
            elif param == "shortcutnode":
                str = bytes(shortcutnode) if SHORTCUT_AVA else "no shortcut node avaliable"
                print ("shortcut node is:" + str)
        elif command.split(" ")[0] == "store":
            fpath = command.split(" ")[1]
            filename = fpath.split("/")[len(fpath.split("/"))]
            if not os.path.isfile(fpath):
                print("File path not valid")
                continue
            else:
                sock_get = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                sock_get.bind((LOCALHOST, self_identifier + FILE_PORT_BASE))
                sock_get.listen(1)
                Send_TCP_msg("STORE:" + filename + ":" + bytes(LOCALHOST) + ":" +
                             bytes(self_identifier + FILE_PORT_BASE),sucnode_1[0],suc_id + TCP_PORT_BASE)
                print("Sending out storing request,listening for reply")
                conn,addr = sock_get.accept()
                info = conn.recv(BUFFER)
                fo = open(fpath,"rb")
                if info == "RECV_READY":
                    print("Request responded.Attempting to transmit file")
                    while True:
                        filedata = fo.read(1024)
                        if not filedata:
                            break
                        sock_get.send(filedata)
                    fo.close()
                conn.close()
                sock_get.close()
                print("File storing success!")

        elif command.split(" ")[0] == "req":
            sock_rec = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            sock_rec.bind((LOCALHOST, self_identifier + FILE_PORT_BASE))
            sock_rec.listen(1)
            filename = command.split(" ")[1]
            Send_TCP_msg("REQ:" + filename + ":" + bytes(LOCALHOST) + ":"
                         + bytes(self_identifier + FILE_PORT_BASE), sucnode_1[0], suc_id + TCP_PORT_BASE)
            print("Sending out request")
            conn,addr = sock_rec.accept()
            info = conn.recv(BUFFER)
            if info == "FILE_READY":
                conn.send("RECV_READY")
                print("File is found ! Receiving ")
                fpath = "localrecv/" + bytes(datetime.datetime.now()) + "_" + filename
                fo = open(fpath,'wb')
                while True:
                    data = conn.recv(BUFFER)
                    if not data:
                        break
                    fo.write(data)
                print("File transmission completed!")
                fo.close()
                conn.close()
                sock_rec.close()


        else:
            print("Invalid command please reinput\n")
            continue




if __name__ == '__main__':
    initialization()

