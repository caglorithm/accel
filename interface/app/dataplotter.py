import matplotlib
matplotlib.use('PS')
import matplotlib.pyplot as plt
import h5py
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import numpy as np
import os

STATIC_IMAGES_DIR = 'app/static/images/'

def plot_last_runs(nRuns = 10, filename = "../log.h5"):
    with h5py.File(filename, mode='r') as h5f:
        runs = list(h5f.keys())
    runs = runs[-nRuns:][::-1]
    for r in runs:
        plot_recording(runName = r, filename = filename)
    return runs
def plot_recording(rInd = -1, runName = None, filename = "../log.h5"):
    if runName is None:
        with h5py.File(filename, mode='r') as h5f:
            runs = list(h5f.keys())
        runName = runs[rInd]
        
    image_dir = os.path.join(STATIC_IMAGES_DIR, "{}.png".format(runName))
    if os.path.isfile(image_dir):
        print("File {} exists...".format(image_dir))
    else:
        with h5py.File(filename, mode='r') as h5f:
            runs = list(h5f.keys())
            if runName is None:
                runName = runs[rInd]
            print("Rendering {}".format(runName))

            ts = h5f[runName]['ts_realtime'][()]
            diffs = h5f[runName]['diffs'][()]
            acts = h5f[runName]['acts'][()]

        times = []
        for i, milli in enumerate(ts):
            times.append(datetime.datetime.fromtimestamp(milli/1000.0))
        times = np.array(times)

        fig = plt.figure(figsize=(14, 4), dpi=100)
        plt.title(runName)
        ax = fig.add_subplot(1, 1, 1)

        ax.plot(times, acts, c='k', lw=3)
        ax.fill_between(times, 0, acts, color='C0', alpha=0.4, label='state')

        thr = 17
        ax.vlines(times[np.argwhere(diffs>thr)], 0, 1, color='red', zorder=1, alpha=0.3)

        ax.set_ylim(0, 1)

        hours = mdates.HourLocator(interval = 1)
        h_fmt = mdates.DateFormatter('%H:%M:%S')
        ax.xaxis.set_tick_params(rotation=90)
        ax.xaxis.set_major_locator(hours)
        ax.xaxis.set_major_formatter(h_fmt)

        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        #ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        #ax.tick_params(direction='out', length=4, width=1, colors='k', labelsize=6)

        #plt.grid()
        #plt.show()
        plt.savefig(image_dir, bbox_inches='tight')
        return fig




