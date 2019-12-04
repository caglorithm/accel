from flask import render_template, request
from app import app

from app.dataplotter import plot_last_runs

@app.route('/')
@app.route('/index')
def index():
    
    nRuns = request.args.get('runs')
    if nRuns is None:
        nRuns = 15
    else:
        try:
            nRuns = int(nRuns)
        except:
            nRuns = 15
    
    user = {'username': 'Caglar' }
    
    
    runNames = plot_last_runs(nRuns)
    
    runs = [
        { 'name' : "2019-12-04-01H-05M-08S"}
    ]
    
    runs = []
    for r in runNames:
        runs.append({ 'name' : r})
    
    return render_template('index.html', title='Home', nRuns = nRuns, runs=runs, user = user)
