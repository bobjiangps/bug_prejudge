import requests
from datetime import datetime
import threading
import multiprocessing

start = datetime.now()

# # serial
# for _ in range(5):
#     response = requests.get("http://10.109.10.193:8080/prejudge/test_round/100345/test_script/2690892/")
#     print(response)

# # threading
# class myThread(threading.Thread):
#     def __init__(self, threadID, name):
#         threading.Thread.__init__(self)
#         self.threadID = threadID
#         self.name = name
#         print("thread id:", self.threadID)
#
#     def run(self):
#         print ("start thread：" + self.name)
#         get_prejudge(self.name)
#         print ("end thread：" + self.name)
#
# def get_prejudge(name):
#     response = requests.get("http://10.109.10.193:8080/prejudge/test_round/100345/test_script/2690892/")
#     print(name, response)
#
# # create new thread
# thread1 = myThread(1, "Thread-1")
# thread2 = myThread(2, "Thread-2")
# thread3 = myThread(3, "Thread-3")
# thread4 = myThread(4, "Thread-4")
# thread5 = myThread(5, "Thread-5")
# # start new thread
# thread1.start()
# thread2.start()
# thread3.start()
# thread4.start()
# thread5.start()
# # wait thread complete
# thread1.join()
# thread2.join()
# thread3.join()
# thread4.join()
# thread5.join()
# print("exit parent process")


# multi-processing
def get_prejudge(name):
    print("start process: ", name)
    response = requests.get("http://10.109.10.193:8080/prejudge/test_round/100345/test_script/2690892/")
    print(name, response)
    print("end process: ", name)

def create_process(name):
    return multiprocessing.Process(target=get_prejudge(name))

pool = multiprocessing.Pool(processes=4)
pool.apply_async(get_prejudge, ("process-1", ))
pool.apply_async(get_prejudge, ("process-2", ))
pool.apply_async(get_prejudge, ("process-3", ))
pool.apply_async(get_prejudge, ("process-4", ))
pool.apply_async(get_prejudge, ("process-5", ))
pool.close()
pool.join()

end = datetime.now()
print(start, "|", end, "|", end-start)


