import os
import numpy as np
import datetime
import matplotlib.dates as mdates
from scipy import signal
import pandas as pd
import h5py

H5_FILE = '../../log.h5'


def get_runs(nruns=5, filename=H5_FILE):
    with h5py.File(filename, mode='r') as h5f:
        runs = list(h5f.keys())
    runs = runs[-nruns:][::-1]
    ts = []
    datas = []
    spikes = []
    for r in runs:
        t, data, diffs = get_data_from_run(runName=r, filename=filename)
        # convert data to pandas dataframe for easy downsampling
        df = data_to_pandas(t, data)
        # downsample, 1T == 1minute
        df = df.resample('1T').mean().bfill()
        df.index = pd.to_datetime(df.index).strftime('%H:%M:%S')

        df2 = get_spike_times(t, diffs)
        
        df2 = df2.resample('1T').max().bfill()
        #df2.index = pd.to_datetime(df2.index).strftime('%H:%M:%S')
        spike = df2[df2['data'].gt(17)].index.strftime('%H:%M:%S').tolist()
        print(spike)

        #t, data = downsample_data(t, data)
        ts.append(df.index)
        datas.append(df['data'])
        spikes.append(spike)
        
    return ts, datas, spikes


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

    times = []
    for i, milli in enumerate(ts):
        times.append(datetime.datetime.fromtimestamp(milli/1000.0))
    times = np.array(times)
    return times, acts, diffs


def data_to_pandas(t, data):
    df = pd.DataFrame({'t': t, 'data': data})
    df = df.set_index('t')
    df['data'] = df['data'].fillna(0)
    # .  # strftime('%H:%M:%S')
    # print(pd.to_datetime(df.index).strftime('%H:%M:%S'))
    # df.index = pd.to_datetime(df.index).strftime('%H:%M:%S')
    # df.index = pd.to_datetime(df.index, format='%H:%M:%S')
    #df.index = df.index.strftime('%H:%M:%S')
    return df


def get_spike_times(t, diffs, thr=17):
    df = pd.DataFrame({'t': t, 'data': diffs})
    df = df.set_index('t')
    return df
    df[df['data'].gt(thr)].index
    print(df[df['data'].gt(thr)].index.strftime('%H:%M:%S'))
    return df[df['data'].gt(thr)].index.strftime('%H:%M:%S')


def downsample_data(t, data, steps=100):
    t_resampled = signal.resample(t, steps)
    data_resampled = signal.resample(data, steps)
    return t_resampled, data_resampled
