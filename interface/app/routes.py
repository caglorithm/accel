from flask import render_template, request
from app import app

#from app.dataplotter import plot_last_runs, plot_recording
from app.get_data import get_runs, get_run_names


@app.route('/')
@app.route('/index')
def index():
    NRUNS_DEFAULT = 5
    n_runs = request.args.get('runs')
    runName = request.args.get('run')

    n_runs = n_runs or NRUNS_DEFAULT

    user = {'username': 'caglorithm'}


    data = get_runs(n_runs)
    runs = []
    for i, (key, value) in enumerate(data.items()):
        runs.append(value)
        runs[i].update({"id" : i})
        runs[i].update({"name" : key})

    return render_template('index.html', n_runs=n_runs, runs=runs, user=user)
