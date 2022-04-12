#!/usr/bin/env python3
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit
import socket,time,socketserver,threading,traceback
import os
from configure import APP_STATIC_TXT
from threading import Lock
import time
#import asyncio

async_mode = None
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

socketio = SocketIO(app, async_mode=async_mode)

thread = None
thread_lock = Lock()

# 连接队列
client_addr = []
client_socket = []

msgdata = ""
data1= 116.359309
data2= 39.986277

#从BaseRequestHandler继承，并重写handle方法
class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    ip = ""
    port = 0
    timeOut = 3600     # 设置超时时间变量

    def setup(self):
        self.ip = self.client_address[0].strip()     # 获取客户端的ip
        self.port = self.client_address[1]           # 获取客户端的port
        self.request.settimeout(self.timeOut)
        print(self.ip+":"+str(self.port)+"连接到服务器！")
        client_addr.append(self.client_address) # 保存到队列中
        client_socket.append(self.request)      # 保存套接字socket

    #循环监听（读取）来自客户端的数据
    def handle(self):
        while True: # while循环
            #当客户端主动断开连接时，self.recv(1024)会抛出异常
            try:
                time.sleep(1)
		#asyncio.sleep(1)
                #一次读取1024字节,并去除两端的空白字符(包括空格,TAB,\r,\n)
                try:
                    #data = str(self.request.recv(1024), 'ascii')
                    data = self.request.recv(1024).decode()
                #     连接超时
                except socket.timeout:
                    print(self.ip+":"+str(self.port)+"接收超时！即将断开连接！")
                    break # 记得跳出while循环

                #self.client_address是客户端的连接(host, port)的元组
                # print("receive from (%r):%r\n" % (self.client_address, data))

                # 判断是否接收到数据
                if data:
                    cur_thread = threading.current_thread()
                    #                    response = bytes("{}: {}".format(cur_thread.name, data), 'ascii')
                    #                    response = bytes("{}: {}".format(cur_thread.name, data), 'ascii')
                    global msgdata
                    msgdata = "Recv from "+str(self.ip)+":"+str(self.port)+", Data:"+str(data)+", "+str(time.ctime())
                    print(msgdata)
                    if(len(data)>17 and data[17]=='A'):
                        global data1
                        global data2
                        # data1=data
                        # data1表示经度
                        data1 = data[32:43]
                        data1=float(data1)
                        data1=int(data1/100)+(data1%100)/60
                        data1=str(data1)

                        data2 = data[19:29]
                        data2 = float(data2)
                        data2 = int(data2 / 100) + (data2 % 100) / 60
                        data2 = str(data2)
                        print("data1:", data1)
                        print("data2:", data2)
                        print(msgdata)


                    with open(os.path.join(APP_STATIC_TXT, 'text.txt'),"a+") as f:
                        f.write(msgdata)
                        f.write("\n")
                        f.close()
                    socketio.emit('server_response', {'data': msgdata})
                    # socketio.send('server_response', {'data': msgdata})

                    # print("Recv from ",self.ip,":",self.port,"data:",data,time.ctime() )
                    self.request.sendall(( '%s %s %s ' % (time.ctime(),cur_thread.name,data)).encode())
            except:
                traceback.print_exc()
                break

    def finish(self):
        print(self.ip+":"+str(self.port)+"断开连接！")
        client_addr.remove(self.client_address)
        client_socket.remove(self.request)

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    ServerStart = False
    pass

HOST, PORT = "127.0.0.1", 80
# 填入自己的服务器IP，腾讯云的需要填入内网IP，这块卡了好久！！！
# HOST, PORT = "103.46.128.46",29668
server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
ip, port = server.server_address
server.ServerStart = False
# Start a thread with the server -- that thread will then start one
# more thread for each request
server_thread = threading.Thread(target=server.serve_forever)
# Exit the server thread when the main thread terminates
server_thread.daemon = True

@app.route('/')
def index():

    print("route_data1:",data1)
    print("route_data2:", data2)
    # return render_template('map1.html', data=data1)  # 渲染模板
    return render_template('map3.html', data1=data1, data2=data2)  # 渲染模板

@app.route('/distance')
def showdistance():
    return render_template('distance.html', data1=data2, data2=data1)  # 渲染模板

def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        socketio.sleep(1)
        count += 1
        socketio.emit('my_response',
                      {'data1': data1, 'data2':data2, 'count': count,'msgdata':msgdata})

@socketio.event
def connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)

if __name__ == '__main__':
    # server.shutdown()
    # server.server_close()
    # app.run()
    #app.run( app, host='127.0.0.1',port = 8000 )


    if len(client_socket) == 0:

        if server.ServerStart:
            pass
        else:
            server_thread.start()
            server.ServerStart = True
        # print("ThreadedTCPServer start!")
    print("Server loop running in thread:", server_thread.name)
    print("server.ServerStart = ", server.ServerStart)

    socketio.run(app, host='127.0.0.1', port=5000)
    # server_thread.start()
    # server.ServerStart = True
