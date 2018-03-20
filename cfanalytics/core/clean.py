import pandas as pd
import numpy as np


import time


from .utils import open_wods


class Clean(object):
    """An object to clean (post-process) downloaded CrossFit open data.
    """
    
    def __init__(self, path):
        """Clean Crossfit open data object.
        
        Pareameters
        ----------
        path : string
            File path.
            
        Returns
        -------
        cfopendata : pd.Dataframe
            Cleaned Crossfit open data.
            
        Example
        -------
        cfa.Clean('Data/Men_Rx_2018_raw')
        """
        self.path = path
        
        # Open file
        self.df = pd.read_pickle(self.path)
        
        # Get year from the file name
        self.year = int(str(self.path[-8:-4]))         
        
        # Get WOD info
        wod_info = open_wods(self.year)
        self.wodscompleted = int(wod_info['wodscompleted'].values)
        self.predictions = wod_info['predictions'].values
        self.totalreps = wod_info['totalreps'].values
        self.timecaps = wod_info['timecaps'].values        
        new_cols = wod_info['dfcheader'].values
        self.scorel = wod_info['scorel'].values
        # Find the column indexes of the score columns
        self.ci = [None] * self.wodscompleted
        for j in range(self.wodscompleted):
            self.ci[j] = self.df.columns.get_loc(self.scorel[j])
        
        # Check file is in the right order
        if int(self.df.loc[0, 'Overall_rank']) != 1:
            raise IOError('File is not in correct order. Should be ascending \
                          rank')
            
        # Initialize new DataFrame
        self.columns = ['User_id', 'Name', 'Height_(m)', 'Weight_(kg)', 'Age',
                        'Region_id', 'Region_name', 'Affiliate_id',
                        'Overall_rank', 'Overall_score', 'Overall_percentile']
        self.columns.extend(new_cols)
        self.cleandata = pd.DataFrame(columns=self.columns)
                
        # Check if file is Rx or Sc
        if 'Rx' in self.path:
            self.scaled = 0
        else:
            self.scaled = 1
            
        # Check if file is Team
        if 'Team' in self.path:
            self.team = 1
        else:
            self.team = 0            
        
        print('Cleaning '+str(self.path))
        start_time = time.time()
                    
        if self.scaled == 0:
            print('Removing lines')
            
            # Remove people who did not enter a single score
            self._rm_all_0s()
            
            # Set scaled as nan and remove all who entered all scaled scores
            self._rm_all_Sc()
            
            # If Rx remove all who entered scaled scores and no scores
            self._rm_all_Sc_and_0s()
        else:
            # Remove all '- s' from scores and convert 0 and empty to NaN            
            self._rm_Sc_str()

            
        print("that took " +\
              str(round((time.time() - start_time) / 60.0, 2)) + " minutes")
        
        print('Cleaning attributes')        
        start_time = time.time()
        
        # Convert the Userid column to integers and move to self.cleandata
        self.cleandata.loc[:,'User_id'] = self.df.loc[:,'User_id'].astype(int)

        self.cleandata.loc[:,'Name'] = self.df.loc[:,'Name']       
        
        # Convert height to SI units (m) and weight to SI units (kg)
        self._height_weight_to_SI() 
                
        # Convert the Age column to integers (Team doesn't have an age)
        if self.team == 0:
            self.cleandata.loc[:,'Age'] = self.df.loc[:,'Age'].astype(int)
        
        # Convert the Regionid column to integers
        self.cleandata.loc[:,'Region_id'] = \
        self.df.loc[:,'Region_id'].astype(int)
        
        self.cleandata.loc[:,'Region_name'] = self.df.loc[:,'Region_name']         
        
        # Convert the Affiliateid to integer
        # Be aware there are 0 values here which indicate no affliate
        # Can't convet to a nan otherwise all other values have to be a float        
        self.cleandata.loc[:, 'Affiliate_id'] = \
        self.df.loc[:, 'Affiliate_id'].astype(int)

        # Convert the Overallrank column to integers
        self.cleandata.loc[:, 'Overall_rank'] = \
        self.df.loc[:, 'Overall_rank'].astype(int)
        
        # Convert the Overallscore column to integers
        self.cleandata.loc[:, 'Overall_score'] = \
        self.df.loc[:, 'Overall_score'].astype(int)
        
        # Add an 'Overall percentile' column      
        self._overall_percentile()
        print("that took " +\
              str(round((time.time() - start_time) / 60.0, 2)) + " minutes")
        
        # Workouts
        for i in range(self.wodscompleted):
            start_time = time.time()
            wod = self.scorel[i].split('_')[0]
            print('Cleaning wod '+wod)
            
            # Convert wod rank to integers
            self.cleandata.loc[:, wod+'_rank'] = \
            self.df.loc[:, wod+'_rank'].values.astype(int)
            
            # Convert score to a pd.Timedelta, integer
            self._extract_score(wod)
            
            # If the score contains any pd.Timedelta order the data so
            # pd.Timedelta is first, followed by integer, then np.nan
            # Then calculate percentile on pd.Timedelta and integers
            if len(self.tdi) > 0:                
                self._wod_percentile_wtd(wod)
                # Don't do rep/time predictions for team. Could add in later.
                if self.team == 0:
                    # If wod has a time cap do predicted time and predicted 
                    # reps to do stats with the whole distribution
                    self._reps_to_time(i, wod)
                    self._time_to_reps(i, wod)
            # Calculate percentiles on integers
            else:
                self._wod_percentile(wod)
            print("that took " +\
                  str(round((time.time() - start_time) / 60.0, 2)) +\
                  " minutes")
       
        # Save data. Remove the '_raw' from the file
        self.dname = self.path[0:-4]
        self.cleandata.to_pickle(self.dname)
        self.cleandata.to_csv(path_or_buf=self.dname+'.csv')         
        

    def _rm_all_0s(self):
        """Remove people who didn't enter a single score.
        Count up from the bottom and find the first person who has entered a 
        score.
        
        Returns
        -------
        cfopendata : pd.Dataframe
            Crossfit open data with less rows.
        """
        l = [None] * self.wodscompleted
        lexpect = [''] * self.wodscompleted 
        lexpect2 = ['0'] * self.wodscompleted
                
        i = len(self.df) - 1
        while i < len(self.df):
            # Populate l
            for j in range(self.wodscompleted):
                l[j] = self.df.iloc[i,self.ci[j]]
            # Check if they are not all either '' or '0'
            if all([l != lexpect, l != lexpect2]):
                self.df = self.df.iloc[:i]
                i = i + len(self.df)
            i -= 1

        self.df = self.df.reset_index(drop=True)
        return self.df
    
    
    def _rm_all_Sc(self):
        """Remove people who didn't enter a Rx score in Rx division.
        And set other Scale values as np.nans.
        
        Returns
        -------
        cfopendata : pd.Dataframe
            Crossfit open data with less rows.
        """
        l = []
        for i in range(self.wodscompleted):
            l.append(self.df.loc[:, self.scorel[i]].values.tolist())
        
        # Create index for nans and change for each coloumn
        ii = np.empty(shape=(self.wodscompleted, len(self.df)), dtype=int)
        ii[:] = -1
        
        # Find scaled inputs and set to nan
        for i in range(self.wodscompleted):
            for j in range(len(self.df)):
                if l[i][j].endswith('- s'):
                    ii[i,j] = j
        
        for i in range(self.wodscompleted):
            tmp = ii[i,:]
            _tmp = tmp[tmp >= 0]
            self.df.iloc[_tmp,self.ci[i]] = np.nan
        
        # If all scores are nan set row to nan and remove
        _ind = pd.isnull(self.df.loc[:,self.scorel]).all(axis=1)
        _in2 = _ind[_ind == True].index.values
        self.df.iloc[_in2,:] = np.nan 
        self.df = self.df.dropna(axis=0, how='all').reset_index(drop=True)
        return self.df


    def _rm_all_Sc_and_0s(self):
        """Remove people who didn't enter a Rx score in Rx division or did not 
        enter a score.
        
        Returns
        -------
        cfopendata : pd.Dataframe
            Crossfit open data with less rows.
        """
        l = []
        for i in range(self.wodscompleted):
            l.append(self.df.loc[:, self.scorel[i]].values.tolist())
            
        # Create index for nans and change for each coloumn
        ii = np.empty(shape=(self.wodscompleted, len(self.df)), dtype=int)
        ii[:] = -1

        # Find empty scores
        for i in range(self.wodscompleted):
            for j in range(len(self.df)):
                if l[i][j] == '0' or l[i][j] == '':
                    ii[i,j] = j
                     
        for i in range(self.wodscompleted):
            tmp = ii[i,:]
            _tmp = tmp[tmp >= 0]
            self.df.iloc[_tmp,self.ci[i]] = np.nan
        
        # If all scores are nan set row to nan and remove
        _ind = pd.isnull(self.df.loc[:,self.scorel]).all(axis=1)
        _in2 = _ind[_ind == True].index.values
        self.df.iloc[_in2,:] = np.nan 
        self.df = self.df.dropna(axis=0, how='all').reset_index(drop=True)
        return self.df       
           

    def _rm_Sc_str(self):
        """Remove the ' - s' from all the scores. and make '0' or '' a np.nan
        
        Returns
        -------
        cfopendata : pd.Dataframe
            Crossfit open data without ' - s' in scores and np.nans.
        """
        l = []; nl = [] 
        for i in range(self.wodscompleted):
            l.append(self.df.loc[:, self.scorel[i]].values.tolist())
            nl.append(self.df.loc[:, self.scorel[i]].values.tolist())
        
        # Create index for nans and change for each coloumn
        ii = np.empty(shape=(self.wodscompleted, len(self.df)), dtype=int)
        ii[:] = -1
        
        # Find scaled inputs and set to nan
        for i in range(self.wodscompleted):
            for j in range(len(self.df)):
                if l[i][j].endswith('- s'):
                    nl[i][j] = l[i][j][0:-4]
                else:
                    ii[i,j] = j
        
        # Add new list back in and nans
        for i in range(self.wodscompleted):
            self.df.iloc[:,self.ci[i]] = nl[i][:]
            tmp = ii[i,:]
            _tmp = tmp[tmp >= 0]
            self.df.iloc[_tmp,self.ci[i]] = np.nan         
        return self.df


    def _height_weight_to_SI(self):
        """Convert height (feet and inches; cms) to SI units (m). and convert
        weight (lbs; kg) to SI units (kg).
        
        Returns
        -------
        cfopendata : pd.Dataframe
            Crossfit open data with height in meters.
        """
        h = self.df.loc[:,'Height'].values.tolist()
        w = self.df.loc[:,'Weight'].values.tolist()
        
        nh = np.empty([len(h)], dtype=np.double)
        nw = np.empty([len(h)], dtype=np.double)
        
        for i, _tmp in enumerate(nh):
            # Height
            if h[i].endswith('"'):
                nh[i] = round((((int(h[i][0]) * 12) +\
                              int(h[i].split('\'')[1].split('"')[0])) *\
                              2.54) / 100.0, 2)
            elif h[i].endswith('m'):
                nh[i] = int(h[i].split(' ')[0]) / 100.0
            elif h[i].endswith('in'):
                nh[i] = round((int(h[i].split(' ')[0]) * 2.54) / 100.0, 2)
            else:
                nh[i] = np.nan
            # Weight
            if w[i].endswith('"'):
                nw[i] = round(int(w[i].split(' ')[0]) / 2.2046 )
            elif w[i].endswith('g'):
                nw[i] = round(int(w[i].split(' ')[0]))
            elif h[i].endswith('lb'):
                nw[i] = round(int(w[i].split(' ')[0]) / 2.2046 )
            else:
                nw[i] = np.nan
        self.cleandata.iloc[:,2] = nh
        self.cleandata.iloc[:,3] = nw      
        return self     

    
    def _overall_percentile(self):
        """Add an overall percentile column.
        
        Returns
        -------
        cfopendata : pd.Dataframe
            Crossfit open data with add overall percentile columns.
        """         
        col = self.df['Overall_rank']
        pct = np.flip(np.round(np.linspace(0, 100, num=len(self.df)),
                               decimals=4), 0)
        # Check for duplications
        pct = self._rm_dups(col, pct)
        self.cleandata.iloc[:,10] = pct
        return self

    
    def _rm_dups(self, col, pct):
        """Remove duplicates in percentiles.
        Check for duplicate scores and give same percentiles
        e.g the ranking of 
        [1,2,2,4,5] # will orginally have percentiles
        [100,75,50,25,0]. This needs to be changed to
        [100,75,75,25,0].    
        
        Parameters
        ----------
        col : pd.DataFrame column
            Column to check for duplicates
        pct : np.array
            Percentile array
            
        Returns
        -------
        pct : np.array
            Percentile array
        """
        df_d = col.duplicated()
        if df_d.any():
            # Loop over the True's
            _ix = df_d.index[df_d == True]
            for i, _index in enumerate(_ix):
                # Replace with the previous value
                pct[int(_index)] = pct[int(_index) - 1]
        return pct


    def _extract_score(self, wod):
        """Convert workout score to a pd.Timedelta or integer.
        
        Parameters
        ----------
        wod : string
            Name of the wod.
        
        Returns
        -------
        cfopendata : pd.Dataframe
            Score are either a pd.Timedelta, integer.
        """
        df_c_name = wod+'_score'
        s = self.df.loc[:,df_c_name].values.tolist()
       
        # Keep track of the indicies
        tdi = np.empty(shape=(0, 0), dtype=int) # time delta
        ii = np.empty(shape=(0, 0), dtype=int) # integers
        ni = np.empty(shape=(0, 0), dtype=int) # np.nans
        
        # initialize new_score array
        _s = self.df.loc[:,df_c_name].reset_index(drop=True)
        for i, _str in enumerate(s):
            # nans
            if isinstance(_str, float):
                ni = np.append(ni, i)
            else:
                # Convert time to time delta
                if ':' in _str:
                    # Some team scores are H:MM:SS
                    if _str.count(':') > 1:                
                        _s[i] = pd.to_timedelta(_str)
                    else:
                        _s[i] = pd.to_timedelta('0:'+_str)
                    tdi = np.append(tdi, i)
                # Convert reps/weight to integers
                else:
                    _s[i] = int(_str.split(" ")[0])
                    # Drop scores of 0 reps/weight
                    if _s[i] > 0:
                        ii = np.append(ii, i)
                    else:
                        _s[i] = np.nan
                        ni = np.append(ni, i)
        self.cleandata.loc[:,df_c_name] = _s.values
        self.tdi = tdi
        self.ii = ii
        self.ni = ni
        return self
    
    
    def _wod_percentile(self, wod):
        """Calculate wod percentile for reps/weight.
        
        Parameters
        ----------
        wod : string
            Name of wod.
        
        Returns
        -------
        cfopendata : pd.Dataframe
            Added percentile column.
        """  
        df_c_name = wod+'_score'
        _s = self.cleandata.loc[:,df_c_name]
        _s_i = _s[self.ii]
        _s_i_sorted = _s_i.sort_values(ascending=False)

        pct = np.flip(np.round(np.linspace(0, 100, num=len(_s_i_sorted)),
                               decimals=4), 0)
        # Remove duplicates        
        pct = self._rm_dups_wod(_s_i_sorted, pct)    
        
        # Check if any nans rows
        if len(self.ni) > 0:
            # Get nan rows
            _s_n = _s[self.ni]
            # Append to s_td_sorted
            _s_i_sorted = _s_i_sorted.append(_s_n)
            # Add nans into pct
            _nan_arr = np.arange(len(_s_i_sorted) - len(pct), dtype=np.double)
            _nan_arr[:] = np.nan
            # Append NaN to pct
            pct = np.append(pct, _nan_arr)

        # Append pct to _s_i_sorted
        _df_i_sorted = _s_i_sorted.to_frame(name = df_c_name)
        _df_i_sorted2 = _df_i_sorted.copy()
        _df_i_sorted2 = _df_i_sorted2.rename(
                columns={wod+'_score': wod+'_percentile'})
        pct = np.transpose(np.expand_dims(pct, axis=0))
        _df_i_sorted2.loc[:] = pct
        # Put back into dataframe index
        _df_i_sorted2.index = _df_i_sorted2.index.map(int)
        _df = _df_i_sorted2.sort_index()
        pct_vals = _df.values
 
        # Add to self.cleandata
        self.cleandata.loc[:, wod+'_percentile'] = pct_vals
        return self


    def _wod_percentile_wtd(self, wod):
        """Calculate wod percentile with Timedelta.
        
        Parameters
        ----------
        wod : string
            Name of wod.
        
        Returns
        -------
        cfopendata : pd.Dataframe
            Added percentile column.
        """
        df_c_name = wod+'_score'
        _s = self.cleandata.loc[:,df_c_name]
        # Get timedelta rows
        _s_td = _s[self.tdi]       
        _s_td_sorted = _s_td.sort_values()
        
        # Check if any integer rows
        if len(self.ii) > 0:
            # Get integers rows
            _s_i = _s[self.ii]
            _s_i_sorted = _s_i.sort_values(ascending=False)
            # Append to s_td_sorted
            _s_td_sorted = _s_td_sorted.append(_s_i_sorted)
            
        pct = np.flip(np.round(np.linspace(0, 100, num=len(_s_td_sorted)),
                               decimals=4), 0)
        # Remove duplicates        
        pct = self._rm_dups_wod(_s_td_sorted, pct)       
 
        # Check if any nans rows
        if len(self.ni) > 0:
            # Get nan rows
            _s_n = _s[self.ni]
            # Append to s_td_sorted
            _s_td_sorted = _s_td_sorted.append(_s_n)
            # Add nans into pct
            _nan_arr = np.arange(len(_s_td_sorted) - len(pct), dtype=np.double)
            _nan_arr[:] = np.nan
            # Append NaN to pct
            pct = np.append(pct, _nan_arr)
            
        # Append pct to _s_td_sorted
        _df_td_sorted = _s_td_sorted.to_frame(name = df_c_name)
        _df_td_sorted2 = _df_td_sorted.copy()
        _df_td_sorted2 = _df_td_sorted2.rename(
                columns={wod+'_score': wod+'_percentile'})
        pct = np.transpose(np.expand_dims(pct, axis=0))
        _df_td_sorted2.loc[:] = pct
        # Put back into dataframe index
        _df_td_sorted2.index = _df_td_sorted2.index.map(int)
        _df = _df_td_sorted2.sort_index()
        pct_vals = _df.values
                
        # Add to self.cleandata
        self.cleandata.loc[:, wod+'_percentile'] = pct_vals
        return self        


    def _rm_dups_wod(self, col, pct):
        """Remove duplicates with of wod scores.

        Parameters
        ----------
        col : pd.DataFrame column
            Column to check for duplicates.
        pct : np.array
            Percentile array.
            
        Returns
        -------
        pct : np.array
            Percentile array.
        """
        df_d = col.duplicated().reset_index(drop=True)
        if df_d.any():
            # Loop over the True's
            _ix = df_d.index[df_d == True]
            for i, _index in enumerate(_ix):
                # Replace with the previous value
                pct[int(_index)] = pct[int(_index) - 1]
        return pct


    def _reps_to_time(self, ix, wod):
        """Calculate predicted time of those who did not finshed in the time 
        cap.
        
        This allows us to compare all athletes who took part in the wod.
        There is no obvious way to do this so my method is simply to assume
        an athelete has a constant pace. Because the score of 'for time' should
        be a time. I will convert reps into time.
        For example if a wod is a 10 min time cap and it requieres you to do 
        100 reps.
        Athlete A finishes within the time cap at 8:00.
        Athlete B only gets to 80 reps within the 10:00 time cap.
        I want to give athlete B a time score therefore if the athlete 
        continued at the current pace how long would it take them to complete
        100 reps
        Athlete B was working at (10 * 60 seconds) / 80 reps which is 7.5
        seconds per rep.
        If athlete B continues for at 7.5 seconds per rep how long will it take
        them to reach 100 reps?
        100 - 80 = 20 reps left; 20 reps at 7.5 reps per second = 20 * 7.5
        = 150 seconds (make sure to round this)
        10 mins + 150 seconds = 12:30 as a predicted time.
        I can now to do stats on A and B and plotting.
        
        Parameters
        ----------
        ix : integer
            for indexing ds['totalreps'] and ds['timecaps'].
        wod : string
            Name of the wod.
            
        Returns
        -------
        cfopendata : pd.Dataframe
            Added predicted_reps column.
        """
        total_reps = self.totalreps[ix]
        time_cap = self.timecaps[ix] * 60 # seconds

        df_c_name = wod+'_score'
        _s = self.cleandata.loc[:,df_c_name]
        
        # Get integer rows
        _s_i = _s[self.ii]
        
        # Convert these reps to time
        p_time = np.full_like(np.arange(len(_s), dtype=np.double), np.nan)
        
        for i, val in _s_i.iteritems():
            reps_per_sec = time_cap / val
            reps_left = total_reps - val
            more_time = round(reps_left * reps_per_sec)
            total_time = time_cap + more_time
            p_time[i] = total_time
             
        # Append timedelta rows 
        _s_tdi = _s[self.tdi]        
        for i, val in _s_tdi.iteritems():        
            p_time[i] = val.seconds
        p_time = pd.to_timedelta(p_time, unit='s')
        
        # Add to self.cleandata
        self.cleandata.loc[:, wod+'_predicted_time'] = p_time
        return self


    def _time_to_reps(self, ix, wod):
        """Calculate predicted reps of those who finshed in the time cap.
        
        This allows us to compare all athletes who took part in the wod.
        There is no obvious way to do this so my method is simply to assume
        an athelete has a constant pace. You could get fancy and use a function
        here which decreases athelte output over time. Maybe anoter day...
        For example if a wod is a 10 min time cap and it requieres you to 100
        reps.
        Athlete A finishes within the time cap at 8:00.
        Athlete B only gets to 80 reps within the 10:00 time cap.
        To compare these we will assume that Athelte A continued at the rate 
        until the end of the time cap that is he carries on with the wod for
        another 2 minutes.
        Athlete A was working at (8 * 60 seconds) / 100 reps which is 4.8
        seconds per rep.
        If they continue for another 2 minutes at 4.8 seconds per rep they 
        would have completed an additional (2 * 60 seconds) / 4.8 which is 25 reps
        (make sure to round this number, can't have half reps unless your name
        is Josh Bridges in 17.4)
        Athlete A's predicted reps are therefore 100 + 25 = 125
        I can now to do stats on A and B and plotting.
        
        Parameters
        ----------
        ix : integer
            for indexing ds['totalreps'] and ds['timecaps'].
        wod : string
            Name of the wod.
            
         Returns
        -------
        cfopendata : pd.Dataframe
            Added predicted_reps column.
        """
        total_reps = self.totalreps[ix]
        time_cap = self.timecaps[ix] * 60 # seconds
        
        df_c_name = wod+'_score'
        _s = self.cleandata.loc[:,df_c_name]

        # Get timedelta rows
        _s_td = _s[self.tdi]
        
        # Convert these times to reps
        p_reps = np.full_like(np.arange(len(_s), dtype=np.double), np.nan)
        for i, val in _s_td.iteritems():
            reps_per_sec = val.seconds / float(total_reps)
            secs_left = time_cap - val.seconds
            more_reps = round(secs_left / reps_per_sec)
            p_reps[i] = int(total_reps + more_reps)
        
        # Append integer rows
        # Check if any integer rows
        if len(self.ii) > 0:
            p_reps[self.ii] = _s[self.ii].values
            
        # Add to self.cleandata
        self.cleandata.loc[:, wod+'_predicted_reps'] = p_reps
        return self