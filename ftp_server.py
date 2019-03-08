''''
ftp 文件服务器
'''

from socket import *
import os, sys
import signal
import time

# 创建监听套接字
HOST = '0.0.0.0'
PORT = 6666
ADDR = (HOST,PORT)
FILE_PATH = 'File_Library/'

class FtpServer(object):
    def __init__(self,connfd):
        self.connfd = connfd
    
    def do_list(self):
        # 获取文件列表
        file_list = os.listdir(FILE_PATH)
        if not file_list:
            self.connfd.send("文件库为空".encode())
            return
        else:
            self.connfd.send(b"OK")
            time.sleep(0.1)

        files = ""
        for file in file_list:
            if file[0] != "." and os.path.isfile(FILE_PATH+file):
                files = files + file + ","
        
        # 将拼接好的字符串传给客户端
        self.connfd.send(files.encode())

    def do_get(self,filename):
        try:
            fd = open(FILE_PATH + filename, 'rb')
        except IOError:
            self.connfd.send('文件不存在'.encode())
            return 
        else:
            self.connfd.send(b'OK')
            time.sleep(0.1)

            # 发送文件内容
            while True:
                data = fd.read(1024)
                if not data:
                    time.sleep(0.1)
                    self.connfd.send(b'##')
                    break
                self.connfd.send(data)

    def do_put(self,filename):
        if os.path.exists(FILE_PATH + filename):
            self.connfd.send('此文件已存在'.encode())
            return

        fd = open(FILE_PATH + filename,'wb')
        self.connfd.send(b'OK')

        # 接收文件
        while True:
            data = self.connfd.recv(1024)
            if data == b"##":
                break 
            fd.write(data)

        fd.close()


# 网络搭建
def main():
    s = socket()
    s.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
    s.bind(ADDR)
    s.listen(5)
    print("Listen the port 6666......")

    # 处理僵尸进程
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)

    def do_request(connfd):
        ftp = FtpServer(connfd)

        while True:
                data = connfd.recv(1024).decode()
                
                if not data or data[0] == "Q":
                    connfd.close()
                    return

                elif data[0] == 'L':
                    ftp.do_list()

                elif data[0] == "G":
                    filename = data.split(' ')[-1]
                    ftp.do_get(filename)

                elif data[0] == "P":
                    filename = data.split(' ')[-1]
                    ftp.do_put(filename) 
              

    # 循环等待客户端连接
    while True:
        try:
            connfd, addr = s.accept()
        except KeyboardInterrupt:
            sys.exit('服务器退出')
        except Exception as e:
            print('Error',e)
            continue
        
        print("连接客户端:",addr)
        
        pid = os.fork() #创建子进程

        if pid == 0:
            s.close()
            do_request(connfd)
            
            os._exit(0)

        #无论父进程或者创建进程失败都是循环接收新的连接
        else:
            connfd.close()

if __name__ == '__main__':
    main()