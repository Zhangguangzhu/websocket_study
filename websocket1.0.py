# -*- coding: utf-8 -*-
import struct, socket, threading, hashlib, base64, queue

class Websocket(threading.Thread):

	def __init__(self, clientsocket, q):
		# threading.Thread.__init__(self)
		super(Websocket, self).__init__()
		self.clientsocket = clientsocket
		self.q = q

	def parseData(self, clientsocket, data):
		enstring = b''
		cnstringlist = []
		cnstring = ''
		if data[0] == 0x88:
			return ''
		else:
			res = data[1] & 0x7f
			if res == 0x7e:
				step = 4
			elif res == 0x7f:
				step = 10
			else:
				step = 2
			mask = data[step:step+4]
			msgdata = data[step+4:]
			for n, c in enumerate(msgdata):
				string = chr(c ^ mask[n % 4])
				if len(string.encode()) == 1:
					enstring +=	string.encode()
				else:
					enstring += b'%s'
					cnstringlist.append(ord(string))
			if len(cnstringlist) >= 3:
				count = int(len(cnstringlist) / 3)
				for i in range(count):
					j = i * 3
					b = bytes([cnstringlist[j], cnstringlist[1+j], cnstringlist[2+j]])
					cnstring += b.decode()
					# print(cnstring)
				enstring = enstring.replace(b'%s%s%s', b'%s').decode()
				finalstr = enstring % tuple(cnstring)
			else:
				finalstr = enstring.decode()
			return finalstr

	def packData(self, message):
		#先添加第一个字节\x81
		header = bytes()
		lenth = len(message.encode())
		header += struct.pack('B', 129)
		#判断数据长度，并添加
		if lenth <= 125:
			header += struct.pack('B', lenth)
		elif lenth <= 65535:
			header += struct.pack('B', 126)
			header += struct.pack('!H', lenth)
		elif lenth <= (2 ^ 64 - 1):
			header += struct.pack('B', 127)
			header += struct.pack('!Q', lenth)
		else:
			print('msg too long')
			return
		return header + bytes(message, encoding='utf-8')

	def sendmessage(self, message):
		msg = self.packData(message)
		self.clientsocket.send(msg)

	def handshaken(self):
		headers = {}
		recvdata = self.clientsocket.recv(1024).decode()
		for line in recvdata.split('\r\n')[1:]:
			if len(line) > 1:
				key, value = line.split(': ', 1)
				headers[key] = value
		Sec_WebSocket_Key = headers['Sec-WebSocket-Key'] + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
		responseKey = 'Sec-WebSocket-Accept: ' + base64.b64encode(hashlib.sha1(bytes(Sec_WebSocket_Key, encoding='utf-8')).digest()).decode() + '\r\n'
		self.clientsocket.send(bytes("HTTP/1.1 101 Web Socket Protocol Handshake\r\n", encoding="utf8"))
		self.clientsocket.send(bytes("Upgrade: websocket\r\n", encoding="utf8"))
		self.clientsocket.send(bytes(responseKey, encoding="utf8"))
		self.clientsocket.send(bytes("Connection: Upgrade\r\n\r\n", encoding="utf8"))
		print('send the hand shake data')


	def run(self):
		self.handshaken()
		while True:
			recvData = self.clientsocket.recv(1024)
			msgData = self.parseData(self.clientsocket, recvData)
			if not msgData:
				self.q.put(self.clientsocket)
				print('quit:', self.clientsocket.getsockname())
				self.clientsocket.close()
				break
			else:
				print(msgData)
				self.sendmessage('哈喽')

class WebsocketServer(object):

	def __init__(self):
		self.Host = '127.0.0.1'
		self.Port = 9999
		self.SerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.SerSocket.bind((self.Host, self.Port))
		self.SerSocket.listen(5)
		self.clientList = {}
		self.q = queue.Queue()

	def start(self):
		print('waiting for connection!')
		if not self.q.empty():
			clientinfo = self.q.get()
			# print('quit:', self.clientList[clientinfo])
			del self.clientList[clientinfo]
		print('online num: %s' % len(self.clientList))
		clientsocket, clientaddr = self.SerSocket.accept()
		print('connection from %s:%s' % (clientaddr[0], clientaddr[1]))
		clientThread = Websocket(clientsocket, self.q)
		self.clientList[clientsocket] = clientaddr
		clientThread.start()


if __name__ == '__main__':
	server = WebsocketServer()
	while True:
		server.start()