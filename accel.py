from SleepLogger import SleepLogger
import matplotlib.pyplot as plt

sl = SleepLogger()

ts_data, ts_realtime_data, raw_data, acts, diffs, delays, states = sl.chunkwise_logger(9999999999990999, 512)
