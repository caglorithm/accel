from flask import render_template, request
from app import app

from app.dataplotter import plot_last_runs, plot_recording
from app.get_data import get_runs, get_run_names


@app.route('/')
@app.route('/index')
def index():
    NRUNS_DEFAULT = 5
    nruns = request.args.get('runs')
    runName = request.args.get('run')

    nruns = nruns or NRUNS_DEFAULT

    user = {'username': 'caglorithm'}

    # if runName is not None:
    #     plot_recording(runName=runName)
    #     runNames = [runName]
    # else:
    #     runNames = plot_last_runs(nRuns)

    runNames = get_run_names(nruns)
    ts, datas, spikes, sleep_durations, deep_durations, light_durations = get_runs(nruns)
    runs = []
    for i, r in enumerate(runNames):
        runs.append({'id': i,
                     'name': r,
                     't': ts[i],
                     'data': datas[i],
                     'spikes': spikes[i],
                     'sleep_duration': sleep_durations[i],
                     'deep_duration': deep_durations[i],
                     'light_duration': light_durations[i]})


    return render_template('index.html', nRuns=nruns, runs=runs, user=user)
