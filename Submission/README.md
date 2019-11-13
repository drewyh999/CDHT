## A Simple Circular Distrubute Hash Table

### 1.Getting started:

---
学生采用本地端口实现，需要首先建立三个节点形成环状的结构，然后才可以进行后续的节点处理

---

 首先建立三个节点（确保得知现在本机的ip地址，我们用10.132.12.61作为例子），每一个节点单独作为一个进程，所以我们需要打开三个终端窗口
 在项目目录下打开三个不同的linux终端或windowpowershell输入以下命令

```
python dht_node_1.py null null //这里建立第一个节点
python dht_node_2.py null 10.132.12.61:30001 //这里建立第二个节点 将ip地址换成您的本机ip即可
python dht_node_3.py null 10.132.12.61:30121 //这里建立第三个节点
```

 在输入命令之后，程序会立刻要求指定后继结点，所以确保三个节点自己都建立之后再给每一个节点指定后继节点<br>
 （程序输出为下）

```
It seems our sucessor node is now not available please specify a new one
input the suc_node ip and UDP port number divided by ':'
```
此时，给第一个节点指定后继节点为 10.132.12.61:30121<br>
给第二个节点指定后继节点为 10.132.12.61:30241<br>
给第三个节点指定后继节点为 10.132.12.61:30001<br>
即可完成三个节点组网，后续的节点可以通过以下命令的方式加入这个环状DHT网络
```bash
python dht_node_/节点号/.py [后继节点ip:port] [前驱节点ip:port]
```
### 2.各种命令介绍

> get sucnode 会返回当前后继节点的信息，如果没有后继节点则会显示后继节点不可用<br>
> get prenode 会返回当前前驱节点信息<br>
> get backupnode 会返回当前节点后继节点的后继节点信息<br>
> get shortcutnode 会返回当前节点的shortcut节点信息<br>
> set sucnode [ip:port] 会根据参数设置当前的后继节点<br>
> set shortcut [shortcutcount] 会根据参数设置shortcut<br>
> set showpingmsg [on/off] 会根据参数打开ping信息的输出，打开或者关闭<br>
> req [filename] 会根据文件名在CDHT网络中查找这个文件<br>
> store [filepath] 会根据文件路径将文件储存在CDHT网络当中<br>



