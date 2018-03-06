import xarray as xr
import numpy as np


def open_wods(year):
    """Information about the Open workouts for each year.
    See https://games.crossfit.com/workouts/open/2018/2
    
    Parameters
    ----------
    year : int
        Year to download crossfit data e.g. 2017.
        
    Returns
    -------
    open_wods : xr.Dataset
        Information about the open work out.
    """
    ds = xr.Dataset()
    _yr = str(year)[2:]
    
    if year == 2017:
        wodscompleted = 5
        units = ['time/reps', 'reps', 'time/reps', 'reps', 'time/reps']
        totalreps = [225, np.inf, 216, np.inf, 440]
        timecaps = [20, 12, 24, 13, 40]
        predictions = [True, False, True, False, True]
        dfheader = []
        dfcheader = []
        scorel = []
        for i in range(wodscompleted):
            w = str(i+1)
            dfheader.append(_yr+'.'+w+' rank')
            dfheader.append(_yr+'.'+w+' score')
            scorel.append(_yr+'.'+w+' score')
            
            dfcheader.append(_yr+'.'+w+' rank')
            dfcheader.append(_yr+'.'+w+' score')
            dfcheader.append(_yr+'.'+w+' percentile')
            if predictions[i]:
                dfcheader.append(_yr+'.'+w+' predicted time')
                dfcheader.append(_yr+'.'+w+' predicted reps')                
    else:
        wodscompleted = 3
        units = ['reps', 'time/reps', 'weight']        
        totalreps = [np.inf, 110, 1] # With timed wods
        timecaps = [20, 12, 12] # With timed wods      
        predictions = [False, True, False]
        dfheader = [_yr+'.1 rank', _yr+'.1 score', _yr+'.2 rank',
                    _yr+'.2 score', _yr+'.2a rank', _yr+'.2a score']
        scorel = [_yr+'.1 score', _yr+'.2 score', _yr+'.2a score']
        dfcheader = [_yr+'.1 rank', _yr+'.1 score', _yr+'.1 percentile',
                     _yr+'.2 rank', _yr+'.2 score', _yr+'.2 percentile',
                     _yr+'.2 predicted time', _yr+'.2 predicted reps',
                     _yr+'.2a rank', _yr+'.2a score', _yr+'.2a percentile']        
        
    ds['units'] = units
    ds['predictions'] = predictions
    ds['totalreps'] = totalreps
    ds['timecaps'] = timecaps   
    ds['dfheader'] = dfheader
    ds['scorel'] = scorel
    ds['dfcheader'] = dfcheader    
    ds['wodscompleted'] = wodscompleted
    return ds