from flask import render_template, request
from app import app

from app.dataplotter import plot_last_runs, plot_recording
from app.get_data import get_runs


@app.route('/')
@app.route('/index')
def index():
    NRUNS_DEFAULT = 3
    nRuns = request.args.get('runs')
    runName = request.args.get('run')

    if nRuns is None:
        nRuns = NRUNS_DEFAULT
    else:
        try:
            nRuns = int(nRuns)
        except:
            nRuns = NRUNS_DEFAULT

    user = {'username': 'caglorithm'}

    if runName is not None:
        plot_recording(runName=runName)
        runNames = [runName]
    else:
        runNames = plot_last_runs(nRuns)

    ts, datas, spikes = get_runs(nRuns)
    runs = []
    for i, r in enumerate(runNames):
        runs.append({'id': i,
                     'name': r,
                     't': ts[i],
                     'data': datas[i],
                     'spikes': spikes[i]})

    legend = 'Monthly Data'
    labels = ["January", "February", "March",
              "April", "May", "June", "July", "August"]
    labels = ts[0]
    values = [10, 9, 8, 7, 6, 4, 7, 8]
    values = datas[0]

    return render_template('index.html', title='Home', nRuns=nRuns, runs=runs, user=user,
                           values=values, labels=labels, legend=legend)
