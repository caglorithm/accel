from flask import render_template, request
from app import app

from app.dataplotter import plot_last_runs, plot_recording

@app.route('/')
@app.route('/index')
def index():
    NRUNS_DEFAULT = 5
    nRuns = request.args.get('runs')
    
    runName = request.args.get('run')
    
    if nRuns is None:
        nRuns = NRUNS_DEFAULT
    else:
        try:
            nRuns = int(nRuns)
        except:
            nRuns = NRUNS_DEFAULT
    
    user = {'username': 'caglorithm' }
    
    if runName is not None:
        plot_recording(runName = runName)
        runNames = [runName]
    else:
        runNames = plot_last_runs(nRuns)
    
    
    runs = []
    for r in runNames:
        runs.append({ 'name' : r})
    
    return render_template('index.html', title='Home', nRuns = nRuns, runs=runs, user = user)
