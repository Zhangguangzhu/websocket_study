# -*- coding: utf-8 -*-
import threading

__author__ = "Kenny.Li"

import Queue
import time
import random

q = Queue.Queue()


class MyThread(threading.Thread):
	def __init__(self, q, t, j):
		super(MyThread, self).__init__()
		self.q = q
		self.t = t
		self.j = j

	def run(self):
		a = 1
		self.q.put(threading.current_thread())
		time.sleep(self.j)


count = 0
threads = []
for i in xrange(15):
	j = random.randint(1, 8)
	threads.append(MyThread(q, i, j))
for mt in threads:
	mt.start()
print "start time: ", time.ctime()
while True:
	if not q.empty():
		b = q.get()
		print b
	if count == 15:
		break