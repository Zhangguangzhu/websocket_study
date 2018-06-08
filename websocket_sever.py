# -*- coding: utf-8 -*-

import socket, struct, base64, hashlib, six


maskcode = b'\x61\x62\x63\x64'
def parse_recv_data(clientSocket, msg):
	en_bytes = b''
	cn_bytes = []
	if len(msg) < 6:
		return ''
	print(msg,type(msg)) #msg为字节型，msg[1]为int型
	v = msg[1] & 0x7f
	if v == 0x7e:
		p = 4
	elif v == 0x7f:
		p = 10
	else:
		p = 2
	mask = msg[p:p + 4]
	# print(mask)
	data = msg[p + 4:]
	for k, v in enumerate(data):
		nv = chr(v ^ mask[k % 4])
		print(nv,ord(nv))
		nv_bytes = nv.encode()
		nv_len = len(nv_bytes)
		if nv_len == 1:
			print(1)
			en_bytes += nv_bytes
		else:
			print(2)
			en_bytes += b'%s'
			cn_bytes.append(ord(nv_bytes.decode()))
	if len(cn_bytes) > 2:
		print(3)
		# 字节数组转汉字
		cn_str = ''
		clen = len(cn_bytes)
		count = int(clen / 3)
		for x in range(0, count):
			i = x * 3
			b = bytes([cn_bytes[i], cn_bytes[i + 1], cn_bytes[i + 2]])
			cn_str += b.decode()
		new = en_bytes.replace(b'%s%s%s', b'%s')
		new = new.decode()
		res = (new % tuple(cn_str))
	else:
		print(4)
		res = en_bytes.decode()

	return res

def packData(message):
	msglen = len(message)
	msgByteList = []
	msgByte = bytes()
	#先添加第一个字节\x81，消息结束，传输文本数据帧
	msgByteList.append(struct.pack('B', 129))
	#设置掩码位与数据长度
	if msglen <= 125:
		maskcode_msglen = msglen
		msgByteList.append(struct.pack('B', maskcode_msglen))
	elif msglen <= 65535:
		msgByteList.append(struct.pack('B', 126))
		msgByteList.append(struct.pack('!H', msglen))
	elif msglen <= (2 ^ 64 -1):
		msgByteList.append(struct.pack('B', 127))
		msgByteList.append(struct.pack('!Q', msglen))
	else:
		print('msg too long!')
		return
	for c in msgByteList:
		msgByte += c
	#添加掩码
	# msgByte += maskcode
	#将数据与掩码作异或
	# for n, c in enumerate(bytes(message, encoding='utf-8')):
	# 	msgByte += chr(c ^ maskcode[n % 4]).encode()
	return msgByte + bytes(message, encoding='utf-8')




def sendMessage(clientSocket, message):
	msgByte = packData(message)
	clientSocket.send(msgByte)
	# msgLen = len(message)
	# backMsgList = []
	# backMsgList.append(struct.pack('B', 129))
	#
	# if msgLen <= 125:
	# 	backMsgList.append(struct.pack('b', msgLen))
	# elif msgLen <= 65535:
	# 	backMsgList.append(struct.pack('b', 126))
	# 	backMsgList.append(struct.pack('>h', msgLen))
	# elif msgLen <= (2 ^ 64 - 1):
	# 	backMsgList.append(struct.pack('b', 127))
	# 	backMsgList.append(struct.pack('>q', msgLen))
	# else:
	# 	print("the message is too long to send in a time")
	# 	return
	# message_byte = bytes()
	# print(type(backMsgList[0]))
	# for c in backMsgList:
	# 	# if type(c) != bytes:
	# 	# print(bytes(c, encoding="utf8"))
	# 	message_byte += c
	# message_byte += bytes(message, encoding="utf8")
	# # print("message_str : ", str(message_byte))
	# # print("message_byte : ", bytes(message_str, encoding="utf8"))
	# # print(message_str[0], message_str[4:])
	# # self.connection.send(bytes("0x810x010x63", encoding="utf8"))
	# clientSocket.send(message_byte)


if __name__ == "__main__":
	headers = {}
	client_list = []
	serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	host = ("127.0.0.1", 8124)
	serverSocket.bind(host)
	serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	serverSocket.listen(5)
	print("server running")
	while True:
		print("getting connection")
		clientSocket, addressInfo = serverSocket.accept()
		# client_list.append(clientSocket)
		# print(client_list)
		print("get connected")
		receivedData = str(clientSocket.recv(2048))
		# print(receivedData)
		entities = receivedData.split("\\r\\n")[1:]
		# print(entities)
		for line in entities:
			if len(line) > 1:
				key, value = line.split(': ', 1)
				# print(key,value)
				headers[key] = value
		Sec_WebSocket_Key = headers["Sec-WebSocket-Key"] + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
		# print("key ", Sec_WebSocket_Key)
		response_key = base64.b64encode(hashlib.sha1(bytes(Sec_WebSocket_Key, encoding="utf8")).digest())
		response_key_entity = "Sec-WebSocket-Accept: " + response_key.decode('utf-8') + "\r\n"
		clientSocket.send(bytes("HTTP/1.1 101 Web Socket Protocol Handshake\r\n", encoding="utf8"))
		clientSocket.send(bytes("Upgrade: websocket\r\n", encoding="utf8"))
		clientSocket.send(bytes(response_key_entity, encoding="utf8"))
		clientSocket.send(bytes("Connection: Upgrade\r\n\r\n", encoding="utf8"))
		print("send the hand shake data")
		while True:
			data = clientSocket.recv(1024)
			parseData = parse_recv_data(clientSocket, data)
			if not parseData:
				print('client closed')
				break
			else:
				print(parseData)
				sendMessage(clientSocket, 'websocket from server\n')