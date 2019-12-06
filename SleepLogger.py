import numpy as np
import time
import threading 
import h5py
import datetime

import config

import drivers.MMA as MMA
from drivers.OLED import OLED

class SleepLogger:
    def __init__(self, log_to_hdf = True, log_to_redis = True):
        
        self.mma8452q = MMA.MMA8452Q()
        self.activity_threshold = config.ACCELEROMETER_ACTIVITY_THRESHOLD
        
        self.LOG_TO_REDIS = config.LOG_TO_REDIS     
        if log_to_redis:
            import redis
            self.r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=0)
        
        self.LOG_TO_HDF = config.LOG_TO_HDF 
        self.dataset_name = datetime.datetime.now().strftime("%Y-%m-%d-%HH-%MM-%SS")
        if log_to_hdf:
            self.H5_FILENAME = "/home/pi/accel/log.h5"
            self.H5_INIT = False
            
        self.OLED_TEXT = False
        self.OLED_PLOT = True
        if True:
            self.oled = OLED()

                
        
        print("Logger loaded")
        
    def getData(self, mma8452q):
        acc = mma8452q.read_accl()
        accl = [acc['x'], acc['y'], acc['z']]
        millis = int(round(time.time() * 1000))
        t = millis
        return t, accl

    def integrate_activity(self, activity, diff, dt, now, last_spike):
        """
        Non-linear synaptic integrator. Sums up activity spikes over time.
        If no spike was detected for a time period larger than `decay_delay`.
        then the activity it will exponentially decay with time constant `decay`
        """
        thresh = self.activity_threshold
        decay = 2 * 60 * 1000.0
        spike_strength = 0.07
        decay_delay = 5 * 60 * 1000.0

        # if spike is larger than noise threshold
        if diff > thresh:
            activity += (1 - activity) * spike_strength
            # note: the lie above should actually be multiplied with dt
            # in order to make the spike strength independent of dt but 
            # since we have to mutiply with dt later for euler integration,
            # the division is skipped here to save time
            last_spike = now # set the time of this spike

        if now - last_spike > decay_delay:
            # only when the last spike was longer ago than decay_time
            # exponentially decay
            activity += - activity / decay * dt

        # limit activity, can undershoot because of large integration timesteps dt
        if activity < 0:
            activity = 0

        # these are our state variables
        return activity, last_spike

    def detect_state(self, activity):
        # if activity crosses a threshold, classify as "deep sleep" => state = 1
        if activity < 0.01:
            return 1
        else:
            return 0

    def adaptive_logger(self, sample_size = 128, verbose = False, log = False, \
                        init_delay = 2, init_activity = 0, init_acc = [0, 0, 0],
                        last_spike = -1e10, \
                        return_delay = False):
        # activity variable integrated in time
        activity = init_activity
        #last_spike = -1e10

        # activity detection threshold of diff value
        activity_threshold = self.activity_threshold

        # sampling speed
        current_delay = init_delay
        min_delay = 2.0
        max_delay = 200.0 #maximum delay ms

        # prepare arrays for storing results
        raw_data = np.zeros((sample_size, 3)) # raw xyz data 
        ts_data = np.zeros((raw_data.shape[0]))
        ts_realtime_data = np.zeros((raw_data.shape[0]))
        delays = np.zeros((raw_data.shape[0]))
        acts = np.zeros((raw_data.shape[0])) # activity data
        diffs = np.zeros((raw_data.shape[0]))
        states = np.zeros((raw_data.shape[0]))

        # start of integration
        start_milli = int(round(time.time() * 1000))

        # get one sample
        last_t, acc = self.getData(self.mma8452q)
        last_acc = acc
        last_draw = last_t

        for i in range(sample_size):
            t, acc = self.getData(self.mma8452q)

            # calcuate diff value
            # fast versin of np.abs(np.mean(acc-last_acc, axis =1)) or so, much faster without numpy
            diff = abs(((acc[0] - last_acc[0]) + (acc[1] - last_acc[1]) + (acc[2] - last_acc[2])) / 3)

            # dt for this sample
            dt = t - last_t

            # one integratin step of the activity 
            activity, last_spike = self.integrate_activity(activity, diff, dt, t, last_spike)

            # increase sampling rate
            if diff > activity_threshold:
                current_delay /= 10
                if current_delay < min_delay:
                    current_delay = min_delay
            else: # or decrease it
                current_delay *= 1.2
                if current_delay > max_delay:
                    current_delay = max_delay

            # detect activity state 
            state = self.detect_state(activity)

            if verbose:
                #print("\r{:.4}          ".format(diff), end='\r')
                print("\rDelay: {}, activity: {:.2}, diff: {:.4}, state: {}          ".format(int(current_delay), activity, diff, state), end='\r')
            
            if self.OLED_TEXT and t - last_draw > 1000:
                self.oled.draw_text("diff: {:.4}\na: {:.2}".format(diff, activity))
                last_draw = t
            
            # store data in time
            raw_data[i, 0] = acc[0]
            raw_data[i, 1] = acc[1]
            raw_data[i, 2] = acc[2]
            ts_data[i] = t - start_milli        
            ts_realtime_data[i] = t
            delays[i] = current_delay
            diffs[i] = diff
            states[i] = state
            acts[i] = activity

            last_acc = acc
            last_t = t
            
            # finally sleep according to current sampling rate
            time.sleep(current_delay / 1000.0)

        return ts_data, ts_realtime_data, raw_data, acts, diffs, delays, states, last_spike

    def log_data(self, ts_data, ts_realtime_data, raw_data, acts, diffs, delays, states):
        """
        Data logger. Logs data into a database or on hdf5 file storage.
        """
        if self.LOG_TO_REDIS:
            threading.Thread(target=self.log_to_redis, \
                             args=(self.r, ts_data, ts_realtime_data, raw_data, acts, diffs, delays, states)).start()
            #self.log_to_redis(self.r, ts_data, ts_realtime_data, raw_data, acts, diffs, delays, states)
        
        if self.LOG_TO_HDF:
            threading.Thread(target=self.log_to_hdf, \
                             args=(ts_data, ts_realtime_data, raw_data, acts, diffs, delays, states)).start()            
            #self.log_to_hdf(ts_data, ts_realtime_data, raw_data, acts, diffs, delays, states)

    def log_to_redis(self, r, ts, ts_realtime, raw_data, acts, diffs, delays, states):
        for i, t in enumerate(ts):
            # prepare storage format
            diff = "{0:.2f}".format(diffs[i])
            activity = "{0:.4f}".format(acts[i])
            delay = "{0:.2f}".format(delays[i])
            state = int(states[i])
            t = int(t)
            t_realtime = int(ts_realtime[i])

            res = r.xadd('accel', {"t" : t , "t_realtime" : t_realtime, "x" : raw_data[i, 0], "y" : \
                                   raw_data[i, 1], "z" : raw_data[i, 2], \
                        'activity' : activity, 'diff' : diff, 'delay' : delay, 'state' : state})
        return res     
            
    def log_to_hdf(self, ts, ts_realtime, raw_data, acts, diffs, delays, states):
        variables = (ts, ts_realtime, raw_data, acts, diffs, delays, states)
        var_strings = ["ts", "ts_realtime", "raw_data", "acts", "diffs", "delays", "states"]
        with h5py.File(self.H5_FILENAME, 'a') as h5f:
            if self.H5_INIT == False:
                self.dataset_name = datetime.datetime.now().strftime("%Y-%m-%d-%HH-%MM-%SS")                
                print("{}/{}: INIT".format(self.H5_FILENAME, self.dataset_name))
                grp = h5f.create_group(self.dataset_name)
                
                for i, var in enumerate(variables):
                    str_var = var_strings[i]
                    if str_var == "raw_data":
                        for k, str_var in enumerate(['x', 'y', 'z']):
                            print("{}/{}: CREATE {}".format(self.H5_FILENAME, self.dataset_name, str_var))
                            grp.create_dataset(str_var, data=var[:, k], compression="gzip", chunks=True, maxshape=(None,)) 
                    else:                                 
                        print("{}/{}: CREATE {}".format(self.H5_FILENAME, self.dataset_name, str_var))
                        grp.create_dataset(str_var, data=var, compression="gzip", chunks=True, maxshape=(None,)) 
                
                self.H5_INIT = True
            else:
                for i, var in enumerate(variables):
                    str_var = var_strings[i]
                    if str_var == "raw_data":                
                        for k, str_var in enumerate(['x', 'y', 'z']):
                            h5f[self.dataset_name][str_var].resize((h5f[self.dataset_name][str_var].shape[0] \
                                                                    + var[:, k].shape[0]), axis = 0)
                            h5f[self.dataset_name][str_var][-var[:, k].shape[0]:] = var[:, k]
                    else:
                        h5f[self.dataset_name][str_var].resize((h5f[self.dataset_name][str_var].shape[0] \
                                                                + var.shape[0]), axis = 0)
                        h5f[self.dataset_name][str_var][-var.shape[0]:] = var                             
                #h5f[self.dataset_name]["diffs"].resize((h5f[self.dataset_name]["diffs"].shape[0] + diffs.shape[0]), axis = 0)
                #h5f[self.dataset_name]["diffs"][-diffs.shape[0]:] = diffs
                print("{}/{}: APPEND ... {}".format(self.H5_FILENAME, self.dataset_name, \
                                                      h5f[self.dataset_name]['diffs'].shape[0]))
                #print(h5f[self.dataset_name]['diffs'].shape[0])       
                
    def chunkwise_logger(self, n_cycles = 10, t_size = 128, init_activity = 0):
        # inialize variables for integration
        current_delay = 2.0
        acts = [0]
        raw_data = [0, 0, 0]
        last_spike = -1e10

        for i in range(n_cycles): 
            # one cycle of logging
            ts_data, ts_realtime_data, raw_data, acts, diffs, delays, states, last_spike = self.adaptive_logger(t_size, \
                                                                                        init_activity = acts[-1], \
                                                                                        init_delay = current_delay, \
                                                                                        init_acc = raw_data[-1], \
                                                                                        last_spike = last_spike, \
                                                                                        verbose=True, log=False,\
                                                                                        return_delay=True)
            if self.OLED_PLOT:
                #self.oled.draw_timeseries(diffs, text = self.dataset_name)
                self.oled.draw_timeseries(diffs, text = "{0:.2f}".format(acts[-1]))
            
            elapsed_time = ts_realtime_data[-1] - ts_realtime_data[0]
            current_delay = delays[-1]

            # throw all data into redis
            threading.Thread(target=self.log_data, args=(ts_data, ts_realtime_data, raw_data, acts, diffs, delays, states)).start()

        return ts_data, ts_realtime_data, raw_data, acts, diffs, delays, states
