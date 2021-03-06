#!/usr/bin/python3
# -*- coding: utf-8 -*-

# @Author  : lijingwei (marscatcn@live.com)
# @FileName: main.py
# @Software: NaiveMQ

# 尝试遵循 Google 的编码风格指引：【指引要求每行不超过 80 字符，这里就先忽略了。。。。。】
# https://zh-google-styleguide.readthedocs.io/en/latest/google-python-styleguide/python_style_rules/

import config

import socket
import argparse
import os
import sys
import json
from collections import deque

TOOL_VERSION = "0.1.0"
CMD_NAME = os.path.basename(__file__)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Super naive tiny message queue suite", epilog=f"example: os.path.basename(__file__) -role mq")
    parser.add_argument('-v', action='version',
                        version='NaiveMQ'+TOOL_VERSION)
    parser.add_argument(
        '--role', help='set instance role')
    
    return parser.parse_args()

ARGS = {}

class MsgBase(object):             # 如果一个类不继承自其它类, 就显式的从object继承。请注意下面的注释写法
    """通用的基础消息类

    【这里写长一些的关于该类的介绍，可以写多行】
    该类定义了本消息队列中通用的消息。消息生产者发往队列的消息（CommitMsg）、消息消费者请求
    取出消息的消息（）、生产者及消费者

    Attributes:
        __auth: 标记消息发出者身份的字符串。无论是中间件还是消息生产、消费者，都根据该字段判断消息发送者的身份，
            系统中各个参与者都只接受 auth 包含在白名单中的消息，否则直接丢弃并给一个身份非法的 ResponseMessage
        capacity: 保存实际消息内容的 JSON 字符串
    """

    msg_kind = 'message base'               # “类变量” ：所有该类的实例共享，类似于 C++ 的 static 类内变量

    def __init__(self, auth, capacity=list()):  # 构造器写法。第一个参数必须是 self ，相当于 this。capacity 的写法是默认参数
        self.__auth = auth                  # 私有函数或变量以两个下划线开头
        self.capacity = capacity            # 在这里面用 self. 形式写的对象，才是属于每个实例自己的成员变量
        print("Construct complete.")

    def get_auth(self) -> str:              # 可以这样指定返回值类型（可选）
        return self.__auth
    
    def obj_to_json(self):                  # 只声明，不实现。需要由子类实现
        pass                                # pass 就是说这里啥也不干，可以用来做暂时不想写的空函数


class CommitMsg(MsgBase):                   # 继承的写法
    """commit类
    """
    def __init__(self, auth, capacity):
        super().__init__(auth, capacity)    # 调用基类构造器的写法。用 super 可避免使用基类名，参数中不需要加 self
        self.type="commit"                  # 子类中新增成员变量
    
    def obj_to_json(self):
        data = [{'auth': self.__auth, 'type': self.type, 'capacity':self.capacity}]
        json_str = json.dumps(data)
        return json_str


class ResponseMsg(MsgBase):
    """这个是返回给 consumer 的
    """
    
    def __init__(self, auth, capacity):
        super().__init__(auth, capacity=capacity)
        self.type="response"

    def obj_to_json(self):
        data = [{'auth': self.__auth, 'type': self.type, 'capacity':self.capacity}]
        json_str = json.dumps(data)
        return json_str

class MsgQueue(object):

    def __init__(self):
        self.msg_queue = deque([])           # python 标准库里面的双向队列

    def appendMsg(self, msg):
        self.msg_queue.append(msg)
        print("current msg_queue: ")
        print(self.msg_queue)
    

class UDPListener(object):
    """UDP 监听器类

    在指定端口监听所有的 UDP 请求
    """

    def __init__(self, port:int=30303):     # 可以用这种写法限制参数类型（可选）
        self.port = port

    def listenUDP(self) -> tuple:
        """ 在当前线程阻塞监听 UDP 端口

        Args:
            port: 监听的本地端口号，默认 30303 （致敬 Ethereum ）

        Returns:
            存储了 data 和 remoteEndpoint 的 tuple，其中 data 是 str，remoteEndpoint 仍然是个 tuple

        Raises:
            IOError: 进行 socket 创建或监听时出现问题
        """
        local_endpoint = ('127.0.0.1', self.port)
        try:
            server = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            server.bind(local_endpoint)
            data = server.recvfrom(1024)                        # udp 用 recvfrom，tcp 用 recv
            remoteEndpoint = tuple([data[1][0], data[1][1]])
            server.sendto("received".encode(), remoteEndpoint)
            return tuple([bytes.decode(data[0]), data[1]])      # data 是 bytes，可以 decode 成 str
        except IOError:                                         # 异常处理写法
            print(IOError)


class UDPSender(object):
    
    def __init__(self) -> None:
        pass

    def send_UDP(self, msg: str, remote_ip: str, remote_port: int=30303):
        bytes_to_send = str.encode(msg)
        server_address_port = (remote_ip, remote_port)
        buffer_size = 1024

        UDP_client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        UDP_client_socket.sendto(bytes_to_send, server_address_port)
        msg_from_server = UDP_client_socket.recvfrom(buffer_size)
        msg = "Message from Server {}".format(msg_from_server[0])
        print(msg)


def main():
    global ARGS
    ARGS = parse_args()
    udp_listener = None                                      # 提前声明，确保变量生命周期及作用域是整个 main()
    udp_sender = None
    message_queue = None

    # if(config.SystemConfig.linux_dist_info):
        # print(config.SystemConfig.linux_dist_info)

    if not ARGS.role:
        print("未选择角色，退出。可选：mq, commiter, consumer")
        sys.exit(1)

    if ARGS.role=="mq":
        udp_listener = UDPListener()
        message_queue = MsgQueue()
        while(1):
            try:
                receivedMsg = udp_listener.listenUDP()[0]    # 收到的消息（json string）
                data = json.loads(receivedMsg)
                if data['type']=='commit':
                    commit_msg = CommitMsg(auth=data['auth'], capacity=data['capacity'])
                    message_queue.appendMsg(commit_msg)
                elif data['type']=='response':
                    print('2: '+data['type'])
            except KeyboardInterrupt as ki:                 # 处理 Ctrl+C 退出的情况. as 是给异常取别名，可根据需要使用
                print("\nCtrl+C pressed. Terminate.")
                sys.exit(1)
        
    elif ARGS.role=="commiter":
        udp_sender = UDPSender()
        udp_sender.send_UDP('{"auth":"lijingwei","type":"commit","capacity":[{"anything":"???wtf"},{"anything":"???wtf"}]}', "127.0.0.1")

    elif ARGS.role=="consumer":
        pass


# 程序的主要功能应该放在一个单独的 main() 中
# 这样可以避免该文件被其他代码导入时的代码意外执行
# 虽然放在这里没什么实际用途，但是是个好习惯，也是符合 Google 规范要求的
if __name__ == "__main__":
    main()