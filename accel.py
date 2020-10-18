from SleepLogger import SleepLogger
import matplotlib.pyplot as plt
import threading 

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

sl = SleepLogger()

#ts_data, ts_realtime_data, raw_data, acts, diffs, delays, states = sl.chunkwise_logger(9999999999990999, 512)
main_thread = sl.start()
# # wait till end of main thread
main_thread.join()
# print("join over.")