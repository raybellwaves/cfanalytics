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
            dfheader.append(_yr+'.'+w+'_rank')
            dfheader.append(_yr+'.'+w+'_score')
            scorel.append(_yr+'.'+w+'_score')
            
            dfcheader.append(_yr+'.'+w+'_rank')
            dfcheader.append(_yr+'.'+w+'_score')
            dfcheader.append(_yr+'.'+w+'_percentile')
            if predictions[i]:
                dfcheader.append(_yr+'.'+w+'_predicted_time')
                dfcheader.append(_yr+'.'+w+'_predicted_reps')                
    else:
        wodscompleted = 5
        units = ['reps', 'time/reps', 'weight', 'time/reps', 'time/reps']        
        totalreps = [np.inf, 110, 1, 928, 165] 
        timecaps = [20, 12, 12, 14, 9]      
        predictions = [False, True, False, True, True]
        dfheader = [_yr+'.1_rank', _yr+'.1_score', _yr+'.2_rank',
                    _yr+'.2_score', _yr+'.2a_rank', _yr+'.2a_score',
                    _yr+'.3_rank', _yr+'.3_score', _yr+'.4_rank',
                    _yr+'.4_score']
        scorel = [_yr+'.1_score', _yr+'.2_score', _yr+'.2a_score',
                  _yr+'.3_score', _yr+'.4_score']
        dfcheader = [_yr+'.1_rank', _yr+'.1_score', _yr+'.1_percentile',
                     _yr+'.2_rank', _yr+'.2_score', _yr+'.2_percentile',
                     _yr+'.2_predicted_time', _yr+'.2_predicted_reps',
                     _yr+'.2a_rank', _yr+'.2a_score', _yr+'.2a_percentile',
                     _yr+'.3_rank', _yr+'.3_score', _yr+'.3_percentile',
                     _yr+'.3_predicted_time', _yr+'.3_predicted_reps',
                     _yr+'.4_rank', _yr+'.4_score', _yr+'.4_percentile',
                     _yr+'.4_predicted_time', _yr+'.4_predicted_reps'] 
        
    ds['units'] = units
    ds['predictions'] = predictions
    ds['totalreps'] = totalreps
    ds['timecaps'] = timecaps   
    ds['dfheader'] = dfheader
    ds['scorel'] = scorel
    ds['dfcheader'] = dfcheader    
    ds['wodscompleted'] = wodscompleted
    return ds