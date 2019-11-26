import threading
import queue


class ClientThread(threading.Thread):
    def __init__(self, workQueue, flag):
        self.workQueue = workQueue
        super().__init__(daemon=flag)

    def run(self):
        while True:
            function, args = self.workQueue.get()
            if len(args) == 0:
                function()
            else:
                function(args)
            self.workQueue.task_done()


class ThreadPool:
    def __init__(self, max_thread_num, flag):
        self.maxThreadNum = max_thread_num
        self.workQueue = queue.Queue()
        self.thread_set = set()
        self.initThreadPool(flag)

    def initThreadPool(self, flag):
        for i in range(self.maxThreadNum):
            thread = ClientThread(self.workQueue, flag)
            self.thread_set.add(thread)
            thread.start()

    def addTask(self, function, *args):
        self.workQueue.put((function, args))
