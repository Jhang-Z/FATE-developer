import socket

# 监听的IP地址和端口号
host = "192.168.40.172"
port = 5000
role =1 

# 创建套接字对象
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

if role == 1:
    # 绑定IP地址和端口号
    sock.bind((host, port))

    # 监听连接
    sock.listen(1)

    # 等待客户端连接
    client_sock, client_addr = sock.accept()

    data = client_sock.recv(1024).decode()
    print("接收到的数据：", data)

    # 向客户端发送数据
    response = 10
    client_sock.sendall(str(response).encode())

    # 关闭连接
    client_sock.close()
    sock.close()
else:

    # 连接到服务器
    sock.connect((host, port))

    # 向服务器发送数据
    message = 20
    sock.sendall(str(message).encode())

    # 接收服务器发送的数据
    data = sock.recv(1024).decode()
    print("接收到的数据：", data)

    # 关闭连接
    sock.close()