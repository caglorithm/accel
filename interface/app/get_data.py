import os
import numpy as np
import datetime
import matplotlib.dates as mdates
from scipy import signal
import pandas as pd
import h5py
import dill

H5_FILE = '../../log.h5'
DATA_DIR = '../../data/'#os.path.join(STATIC_IMAGES_DIR, "{}.png".format(runName))
PROCESSED_DATA_DIR = '../../data/processed/'##os.path.join(DATA_DIR, "/processed/")

def get_run_names(nruns=5, filename=H5_FILE):
    with h5py.File(filename, mode='r') as h5f:
        runs = list(h5f.keys())
    runs = runs[-nruns:][::-1]
    return runs

def get_runs(nruns=5, h5_filename=H5_FILE):

    runs = get_run_names(nruns, h5_filename)

    data = {}

    for run_name in runs:
        data[run_name] = {}
        df = load_run_data(run_name, h5_filename)

        # get activity spikes
        diff_thrs = 15
        spike_list = df[df['diffs'].gt(diff_thrs)].index.strftime('%H:%M:%S').tolist()

        # get deep sleep duration
        sleep_duration, deep_duration, light_duration = get_sleep_stage_durations(df)

        # time in HH:MM:SS
        t = df.index.strftime('%H:%M:%S')

        # activity
        activity = df['data']

        # states
        states = df['states']
        
        # pack data
        data[run_name]['deep_duration'] = deep_duration
        data[run_name]['light_duration'] = light_duration
        data[run_name]['sleep_duration'] = sleep_duration
        data[run_name]['t'] = t
        data[run_name]['activity'] = activity
        data[run_name]['states'] = states
        data[run_name]['spikes'] = spike_list

    return data


def data_to_pandas(t, data, diffs, states):
    df = pd.DataFrame({'t': t, 'data': data, 'diffs' : diffs, 'states' : states})
    df = df.set_index('t')
    df['data'] = df['data'].fillna(0)
    df['diffs'] = df['diffs'].fillna(0)
    return df

def process_data(t, data, diffs, states):
    df = data_to_pandas(t, data, diffs, states)
    # downsample, 1T == 1minute
    df = df.resample('1T').agg({'data':'mean', 'diffs':'max', 'states':'last'}).bfill()
    df.index = pd.to_datetime(df.index)
    return df

def get_data_from_run(rInd=-1, runName=None, filename=H5_FILE):
    if runName is None:
        with h5py.File(filename, mode='r') as h5f:
            runs = list(h5f.keys())
        runName = runs[rInd]

    with h5py.File(filename, mode='r') as h5f:
        runs = list(h5f.keys())
        if runName is None:
            runName = runs[rInd]
        print("Getting data from {}".format(runName))

        ts = h5f[runName]['ts_realtime'][()]
        diffs = h5f[runName]['diffs'][()]
        acts = h5f[runName]['acts'][()]
        states = h5f[runName]['states'][()]
    
    # convert loaded data into datetime
    times = []
    for i, milli in enumerate(ts):
        times.append(datetime.datetime.fromtimestamp(milli/1000.0))
    times = np.array(times)
    df = process_data(times, acts, diffs, states)
    return df

def load_run_data(run_name, h5_filename):
    # check if preprocessed data is already available
    data_filename = os.path.join(PROCESSED_DATA_DIR, f"{run_name}.dill")
    if os.path.isfile(data_filename):
        print(f"File {data_filename} exists...")
        df = dill.load(open(data_filename, "br+"))
    else:
        df = get_data_from_run(runName=run_name, filename=h5_filename)
        #df = process_data(t, activity, diffs)
        print(f"Saving {data_filename}.")
        dill.dump(df, open(data_filename, "bw+"))    
    return df



def get_spike_times(t, diffs, thr=17):
    df = pd.DataFrame({'t': t, 'data': diffs})
    df = df.set_index('t')
    return df
    df[df['data'].gt(thr)].index
    return df[df['data'].gt(thr)].index.strftime('%H:%M:%S')

def get_sleep_stage_durations(df):
    activity_threshold = 0.05
    deep_duration = len(df[df['data'].le(activity_threshold)].index)
    sleep_duration = len(df)
    light_duration = sleep_duration - deep_duration
    return sleep_duration, deep_duration, light_duration

def downsample_data(t, data, steps=100):
    t_resampled = signal.resample(t, steps)
    data_resampled = signal.resample(data, steps)
    return t_resampled, data_resampled
