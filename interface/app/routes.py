import logging

from flask import render_template, request
from app import app

#from app.dataplotter import plot_last_runs, plot_recording
from app.get_data import get_runs, get_run_names

# some_file.py
import sys
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '../../')
try:
    from SleepLogger import SleepLogger
except ImportError:
    logging.warn("SleepLogger could not be imported")
    class SleepLogger():
        def start(self):
            return 1
        def stop(self):
            return 2

sl = None

@app.route('/')
@app.route('/index')
def index():
    NRUNS_DEFAULT = 5
    n_runs = request.args.get('runs')
    run_name = request.args.get('run')

    n_runs = n_runs or NRUNS_DEFAULT

    user = {'username': 'caglorithm'}


    data = get_runs(n_runs, run_name = run_name)
    runs = []
    for i, (key, value) in enumerate(data.items()):
        runs.append(value)
        runs[i].update({"id" : i})
        runs[i].update({"name" : key})

    return render_template('index.html', n_runs=n_runs, runs=runs, user=user)

@app.route('/start')
def start():
    global sl
    if sl is None:
        sl = SleepLogger()
        sl.start()
        return render_template('tracker.html', status = "started")
    else:
        return render_template('tracker.html', status = "is already running")        

@app.route('/stop')
def stop():
    global sl
    if sl is not None:
        sl.stop()
        sl = None
        # process newest dataset
        _ = get_runs(nruns=1)
        return render_template('tracker.html', status = "stopped")
    else:
        return render_template('tracker.html', status = "is not running")