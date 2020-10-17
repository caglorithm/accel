import numpy as np
import time
import threading 
import h5py
import datetime
import logging
import config

import drivers.MMA as MMA
from drivers.OLED import OLED

from Stimulus import AudioStimulus

class SleepLogger:
    def __init__(self, log_to_hdf = True, stimulus = config.STIMULUS_ACTIVE):
        """
        Sleep logger with adaptive sampling and various logging methods.
        Provides current sleep state data to other objects.
        """
        # Initiate sleep state variables
        self.diff = None # current movement magnitude
        self.diffs = None # past movement magnitudes
        self.activity = None # current activity level
        self.state = None # current sleep state
        
        # Initiate control variables
        self.run = True
        
        # Initiate accelerometer
        self.mma8452q = MMA.MMA8452Q()
        self.activity_threshold = config.ACCELEROMETER_ACTIVITY_THRESHOLD
        
        # Initiate logging
        self.dataset_name = datetime.datetime.now().strftime("%Y-%m-%d-%HH-%MM-%SS")

        self.LOG_TO_REDIS = config.LOG_TO_REDIS     
        if self.LOG_TO_REDIS:
            import redis
            self.r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=0)
            logging.info(f"Logging to Redis server {config.REDIS_HOST}:{config.REDIS_PORT}")
        
        self.LOG_TO_HDF = config.LOG_TO_HDF 
        if self.LOG_TO_HDF:
            self.H5_FILENAME = f"/home/pi/accel/{config.HDF_FILE}"
            self.H5_INIT = False
            logging.info("Logging to HDF file: {}.".format(self.H5_FILENAME))
            
        # Initiate Display
        self.OLED_TEXT = False
        self.OLED_PLOT = True
        if True:
            self.oled = OLED()

        # Initiate Stimulus module
        if stimulus:
            self.audiostim = AudioStimulus()
            logging.info("Stimulus module loaded")

        logging.info("Logger loaded")
        
    def get_accel_data(self, mma8452q):
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
        decay = config.ACTIVITY_DECAY_CONSTANT
        spike_strength = config.ACTIVITY_SPIKE_STRENGTH
        decay_delay = config.ACTIVITY_DECAY_DELAY

        # if spike is larger than noise threshold
        if diff > thresh:
            activity += (1.0 - activity) * spike_strength
            # note: the lie above should actually be multiplied with dt
            # in order to make the spike strength independent of dt but 
            # since we have to mutiply with dt later for euler integration,
            # the division is skipped here to save time
            last_spike = now # set the time of this spike

        if now - last_spike > decay_delay and activity > config.ACTIVITY_LOWER_BOUND:
            # only when the last spike was longer ago than decay_delay
            # exponentially decay
            activity += - activity / decay * dt

        # limit activity, can undershoot because of large integration timesteps dt
        if activity < config.ACTIVITY_LOWER_BOUND:
            activity = 0.0

        # these are our state variables
        return activity, last_spike

    def detect_state(self, activity):
        # if activity crosses a threshold, classify as "deep sleep" => state = 1
        if activity < config.ACTIVITY_THRESHOLD_DEEP_SLEEP:
            return config.SLEEP_STATE_DEEP
        elif activity < config.ACTIVITY_THRESHOLD_WAKE:
            return config.SLEEP_STATE_LIGHT
        else:
            return config.SLEEP_STATE_WAKE
    
    def update_state_variables(self, diff=None, diffs=None, activity=None, state=None):
        if diff is not None:
            self.diff = diff # current movement magnitude
        if diffs is not None:
            self.diffs = difs # past movement magnitudes
        if activity is not None:
            self.activity = activity # current activity level
        if state is not None:
            self.state = state # current sleep state

    def trigger_stimulus(self):
        """Triggers the audio stimulus if in deep sleep and turns it off else.
        """
        if self.state == config.SLEEP_STATE_DEEP:
            if not self.audiostim.isActive:
                print("STARTING STIMULUS")
                self.audiostim.start_stimulus()
                
        else:
            if self.audiostim.isActive:
                print("STOPPING STIMULUS")
                self.audiostim.stop_stimulus()
                

    def adaptive_logger(self, sample_size = 128, \
                        init_delay = 2, init_activity = 0.0, init_acc = [0.0, 0.0, 0.0],
                        last_spike = -1e10, \
                        return_delay = False):
        # activity variable integrated in time
        activity = init_activity
        #last_spike = -1e10

        # activity detection threshold of diff value
        activity_threshold = self.activity_threshold

        # sampling speed
        current_delay = init_delay
        min_delay = config.LOGGER_MIN_DELAY
        max_delay = config.LOGGER_MAX_DELAY #maximum delay ms

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
        last_t, acc = self.get_accel_data(self.mma8452q)
        last_acc = acc
        last_draw = last_t

        for i in range(sample_size):
            t, acc = self.get_accel_data(self.mma8452q)

            # calcuate diff value
            # fast versin of np.abs(np.mean(acc-last_acc, axis =1)) or so, much faster without numpy
            diff = abs(((acc[0] - last_acc[0]) + (acc[1] - last_acc[1]) + (acc[2] - last_acc[2])) / 3)

            # dt for this sample
            dt = t - last_t

            # one integratin step of the activity 
            activity, last_spike = self.integrate_activity(activity, diff, dt, t, last_spike)

            # dynamic integration step size depending on activity level:
            # if there is a lot going on, sampling rate will go up
            # if there is no activity, samnpling rate will drop
            # increase sampling rate
            if diff > activity_threshold:
                current_delay /= config.DELAY_DIVIDE_BY
                if current_delay < min_delay:
                    current_delay = min_delay
            else: # or decrease it
                current_delay *= config.DELAY_MULTIPLY_WITH
                if current_delay > max_delay:
                    current_delay = max_delay

            # detect sleep state from activity level
            state = self.detect_state(activity)
            
            self.update_state_variables(diff=diff, activity=activity, state=state)

            self.trigger_stimulus()

            if config.VERBOSE_OUTPUT:
                print("\rDelay: {}, activity: {:.2}, diff: {:.4}, state: {}          "\
                      .format(int(current_delay), activity, diff, state), end='\r')
            
            # store data in time chunks
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
            time.sleep(current_delay / 1000.0) # seconds

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
            
    def log_to_hdf(self, ts, ts_realtime, raw_data, acts, diffs, delays, states, verbose=False):
        variables = (ts, ts_realtime, raw_data, acts, diffs, delays, states)
        var_strings = ["ts", "ts_realtime", "raw_data", "acts", "diffs", "delays", "states"]
        with h5py.File(self.H5_FILENAME, 'a') as h5f:
            if self.H5_INIT == False:
                self.dataset_name = datetime.datetime.now().strftime("%Y-%m-%d-%HH-%MM-%SS")  
                if config.VERBOSE_OUTPUT:
                    logging.info("{}/{}: INIT".format(self.H5_FILENAME, self.dataset_name))
                grp = h5f.create_group(self.dataset_name)
                
                for i, var in enumerate(variables):
                    str_var = var_strings[i]
                    if str_var == "raw_data":
                        for k, str_var in enumerate(['x', 'y', 'z']):
                            if config.VERBOSE_OUTPUT:
                                logging.info("{}/{}: CREATE {}".format(self.H5_FILENAME, self.dataset_name, str_var))
                            grp.create_dataset(str_var, data=var[:, k], compression="gzip", chunks=True, maxshape=(None,)) 
                    else:   
                        if config.VERBOSE_OUTPUT:
                            logging.info("{}/{}: CREATE {}".format(self.H5_FILENAME, self.dataset_name, str_var))
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
                if config.VERBOSE_OUTPUT:
                    logging.info("{}/{}: APPEND ... {}".format(self.H5_FILENAME, self.dataset_name, \
                                                      h5f[self.dataset_name]['diffs'].shape[0]))      
                
    def chunkwise_logger(self, n_cycles = 10, t_size = 128, init_activity = 0.0, verbose=True):
        # inialize variables for integration
        current_delay = 2.0
        acts = [0.0]
        raw_data = [0.0, 0.0, 0.0]
        last_spike = -1e10

        for i in range(n_cycles): 
            # one cycle of logging
            if self.run:
                # run the next chunk with the last values as initial conditions
                ts_data, ts_realtime_data, raw_data, acts, diffs, delays, states, last_spike = self.adaptive_logger(t_size, \
                                                                                        init_activity = acts[-1], \
                                                                                        init_delay = current_delay, \
                                                                                        init_acc = raw_data[-1], \
                                                                                        last_spike = last_spike, \
                                                                                        return_delay=True)
            else:
                if config.VERBOSE_OUTPUT:
                    logging.info("Logging stopped")
                
            if self.OLED_PLOT:
                # stitch together the object to send to the OLED interfacer thread
                display_input = {}
                display_input['timeseries'] = diffs
                display_input['status'] = "{0:.2f}".format(acts[-1])
                display_input['trigger'] = True if int(states[-1]) == config.SLEEP_STATE_DEEP else False
                threading.Thread(target=self.oled.draw_display, args=(display_input,)).start()                
                #self.oled.draw_timeseries(diffs, text = "{0:.2f}".format(acts[-1]))
            
            elapsed_time = ts_realtime_data[-1] - ts_realtime_data[0]
            current_delay = delays[-1]

            # throw all data into redis
            threading.Thread(target=self.log_data, args=(ts_data, ts_realtime_data, raw_data, acts, diffs, delays, states)).start()

        return ts_data, ts_realtime_data, raw_data, acts, diffs, delays, states
