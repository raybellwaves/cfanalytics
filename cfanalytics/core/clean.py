import pandas as pd
import numpy as np

import time
from functools import reduce


class Clean(object):
    """An object to clean download CrossFit open data.
    """
    
    def __init__(self, path, wods):
        """Clean Crossfit open data object.
        
        Parameters
        ----------
        path : string
            File path.
        wods : pd.DataFrame
            Type of wods e.g. contains if wod had time cap
            
        Returns
        -------
        cfopendata : pd.Dataframe
            Cleaned Crossfit open data.
        """
        self.path = path
        # Open file
        self.df = pd.read_pickle(self.path)
        self.wods = wods
        
        # Check file is in the right order
        if int(self.df.iloc[0, 8]) != 1:
            raise IOError('File is not in correct order. Should be ascending \
                          rank')
        
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
        # Work as year as 4 characters before '_raw'
        self.year = int(str(self.path[-8:-4]))
        self.yearwod = int(str(self.path[-6:-4]))
        
        print('Cleaning '+str(self.path))
        start_time = time.time()
        
        # Check how many workouts have been compltes
        if self.df.iloc[0, -1] is None:
            # NaN the workouts which are not complete
            self._empty_to_nan()
        else:            
            self.wodscompleted = 5
            
        if self.scaled == 0:
            print('Removing lines')
            # Remove people who did not enter a single score if all 5 
            # workouts have been complete  
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
        start_time = time.time() # Start time
        # Convert the Userid column to integers
        self.df['Userid'] = self.df.Userid.astype(int)
              
        # Convert height to SI units (m) and weight to SI units (kg)
        self._height_weight_to_SI()
                
        # Convert the Age column to integers
        # Team doesn't have an age
        if self.team == 0:
            self.df['Age'] = self.df.Age.astype(int)
        
        # Convert the Regionid column to integers
        self.df['Regionid'] = self.df.Regionid.astype(int)
        
        # Convert the Affiliateid to integer
        self.df['Affiliateid'] = self.df.Affiliateid.astype(int)
        # Be aware there are 0 values here which indicate no affliate
        # Can't convet to a nan otherwise all other values have to be a float
        
        # Convert the Overallrank column to integers
        self.df['Overallrank'] = self.df.Overallrank.astype(int)
        
        # Convert the Overallscore column to integers
        self.df['Overallscore'] = self.df.Overallscore.astype(int)
        
        # Add an 'Overallpercentile' column      
        self._overall_percentile()
        print("that took " +\
              str(round((time.time() - start_time) / 60.0, 2)) + " minutes")
        
        # Workouts
        for i in range(1, self.wodscompleted + 1):
            print('Cleaning wod '+str(i))
            start_time = time.time()
            # Convert wod_rank to integers
            self.df[str(self.yearwod)+'.'+str(i)+'_rank'] = \
            self.df[str(self.yearwod)+'.'+str(i)+'_rank'].astype(int)
            
            # Convert _score to a pd.Timedelta, integer or np.nan
            self._extract_score(i)
            
            # If the score contains any pd.Timedelta order the data so
            # pd.Timedelta is first, followed by integer, then np.nan
            # Then calculate percentile on pd.Timedelta and integers
            if len(self.tdi) > 0:
                self._wod_percentile_wtd(i)
 
                # Don't do rep/time predictions for team.
                # Could add in later
                if self.team == 0:
                    # If wod has a time cap do predicted reps to comapre times and 
                    # reps
                    wod_type = self.wods.loc[str(self.year), 'week'+str(i)]
                    if wod_type.split(' ')[-1] == 'cap':
                        self._time_to_reps(i, wod_type)
                    if wod_type.split(' ')[-1] == 'time':
                        self._reps_to_time(i, wod_type) 
            # Calculate percentiles on integers
            else:
                self._wod_percentile(i)
            print("that took " + str(round((time.time() - start_time) / 60.0, 2)) + " minutes")
       
        # Save data
        # Remove the '_raw' from the file
        self.dname = self.path[0:-4]
        self.df.to_pickle(self.dname)
        self.df.to_csv(path_or_buf=self.dname+'.csv')         
        

    def _rm_all_0s(self):
        """Remove people who didn't enter a single score.
        
        Returns
        -------
        cfopendata : pd.Dataframe
            Crossfit open data with less rows.
        """
        # Count up from the bottom and find first the first person who doesn't 
        #have all 0's or ''
        i = len(self.df) - 1
        while i < len(self.df):
            # In 2018 no scores are ''
            if self.year == 2018:
                # Need to know how many wods have been complete
                # This is horrible coding but i'm too lazy to clean it up for
                # the time being
                if self.wodscompleted == 1:
                    if self.df.iloc[i,11] != '':
                        self.df = self.df.iloc[:i]
                        i = i + len(self.df)
                elif self.wodscompleted == 2:
                    if self.df.iloc[i,11] != '' or self.df.iloc[i,13] != '':
                        self.df = self.df.iloc[:i]
                        i = i + len(self.df)
                elif self.wodscompleted == 3:
                    if self.df.iloc[i,11] != '' or self.df.iloc[i,13] != '' or\
                    self.df.iloc[i,15] != '':
                        self.df = self.df.iloc[:i]
                        i = i + len(self.df)
                elif self.wodscompleted == 4:
                    if self.df.iloc[i,11] != '' or self.df.iloc[i,13] != '' or\
                    self.df.iloc[i,15] != '' or self.df.iloc[i,17] != '':
                        self.df = self.df.iloc[:i]
                        i = i + len(self.df)
                else:                        
                    if self.df.iloc[i,11] != '' or self.df.iloc[i,13] != '' or\
                    self.df.iloc[i,15] != '' or self.df.iloc[i,17] != '' or\
                    self.df.iloc[i,19] != '':
                        self.df = self.df.iloc[:i]
                        i = i + len(self.df)                               
            else:
                if self.df.iloc[i,11] != '0' or self.df.iloc[i,13] != '0' or\
                self.df.iloc[i,15] != '0' or self.df.iloc[i,17] != '0' or\
                self.df.iloc[i,19] != '0':
                    self.df = self.df.iloc[:i]
                    i = i + len(self.df) # Make i big to escape
            i -= 1
        return self.df.reset_index(drop=True)
    
    
    def _rm_all_Sc(self):
        """Remove people who didn't enter a Rx score in Rx division.
        And set other Scale values as np.nans
        
        Returns
        -------
        cfopendata : pd.Dataframe
            Crossfit open data with less rows.
        """
        w1 = self.df.iloc[:,11].values.tolist()
        w2 = self.df.iloc[:,13].values.tolist()
        w3 = self.df.iloc[:,15].values.tolist()
        w4 = self.df.iloc[:,17].values.tolist()
        w5 = self.df.iloc[:,19].values.tolist()
        
        w1i = np.empty(shape=(0, 0), dtype=int)
        w2i = np.empty(shape=(0, 0), dtype=int)
        w3i = np.empty(shape=(0, 0), dtype=int)
        w4i = np.empty(shape=(0, 0), dtype=int)
        w5i = np.empty(shape=(0, 0), dtype=int)
        
        for i, _tmp in enumerate(w1):
            if w1[i].endswith('- s'):
                w1i = np.append(w1i, i)
            if not isinstance(w2[i], float):   
                if w2[i].endswith('- s'):
                    w2i = np.append(w2i, i)
            if not isinstance(w3[i], float):                    
                if w3[i].endswith('- s'):
                    w3i = np.append(w3i, i)                
            if not isinstance(w4[i], float): 
                if w4[i].endswith('- s'):
                    w4i = np.append(w4i, i)
            if not isinstance(w5[i], float):
                if w5[i].endswith('- s'):
                    w5i = np.append(w5i, i)
                
        self.df.iloc[w1i,11] = np.nan
        self.df.iloc[w2i,13] = np.nan
        self.df.iloc[w3i,15] = np.nan
        self.df.iloc[w4i,17] = np.nan
        self.df.iloc[w5i,19] = np.nan
        
        # Find eduplicates in np array
        _tmp = reduce(np.intersect1d, (w1i, w2i, w3i, w4i, w5i))
        self.df.iloc[_tmp,:] = np.nan
        # Set rows with nans in scores to nans
        _ind = pd.isnull(self.df.iloc[:,[11,13,15,17,19]]).all(axis=1)
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
        w1 = self.df.iloc[:,11].values.tolist()
        w2 = self.df.iloc[:,13].values.tolist()
        w3 = self.df.iloc[:,15].values.tolist()
        w4 = self.df.iloc[:,17].values.tolist()
        w5 = self.df.iloc[:,19].values.tolist()
        
        w1i = np.empty(shape=(0, 0), dtype=int)
        w2i = np.empty(shape=(0, 0), dtype=int)
        w3i = np.empty(shape=(0, 0), dtype=int)
        w4i = np.empty(shape=(0, 0), dtype=int)
        w5i = np.empty(shape=(0, 0), dtype=int)        
        for i, _tmp in enumerate(w1):
            if w1[i] == '0':
                w1i = np.append(w1i, i)
            if w2[i] == '0':
                w2i = np.append(w2i, i)               
            if w3[i] == '0':                
                w3i = np.append(w3i, i)                
            if w4[i] == '0':
                w4i = np.append(w4i, i)
            if w5[i] == '0':
                w5i = np.append(w5i, i)
                
        self.df.iloc[w1i,11] = np.nan
        self.df.iloc[w2i,13] = np.nan
        self.df.iloc[w3i,15] = np.nan
        self.df.iloc[w4i,17] = np.nan
        self.df.iloc[w5i,19] = np.nan
        
        # Remove NaNs if in all score columns
        _ind = pd.isnull(self.df.iloc[:,[11,13,15,17,19]]).all(axis=1)
        _in2 = _ind[_ind == True].index.values
        self.df.iloc[_in2,:] = np.nan        
        self.df = self.df.dropna(axis=0, how='all').reset_index(drop=True)    
        return self.df        
           

    def _rm_Sc_str(self):
        """Remove the ' - s' from all the scores. and make 0 or'' a np.nan
        
        Returns
        -------
        cfopendata : pd.Dataframe
            Crossfit open data without ' - s' in scores and np.nans.
        """
        w1 = self.df.iloc[:,11].values.tolist()
        w2 = self.df.iloc[:,13].values.tolist()
        w3 = self.df.iloc[:,15].values.tolist()
        w4 = self.df.iloc[:,17].values.tolist()
        w5 = self.df.iloc[:,19].values.tolist()
        
        nw1 = [None] * len(w1)
        nw2 = [None] * len(w2)
        nw3 = [None] * len(w3)
        nw4 = [None] * len(w4)
        nw5 = [None] * len(w5)        

        w1i = np.empty(shape=(0, 0), dtype=int)
        w2i = np.empty(shape=(0, 0), dtype=int)
        w3i = np.empty(shape=(0, 0), dtype=int)
        w4i = np.empty(shape=(0, 0), dtype=int)
        w5i = np.empty(shape=(0, 0), dtype=int)
        for i, _tmp in enumerate(w1):
            if w1[i].endswith('- s'):
                nw1[i] = w1[i][0:-4]
            if not isinstance(w2[i], float):   
                if w2[i].endswith('- s'):
                    nw2[i] = w2[i][0:-4]
                else:
                    w2i = np.append(w2i, i)
            if not isinstance(w3[i], float):   
                if w3[i].endswith('- s'):
                    nw3[i] = w3[i][0:-4]
                else:
                    w3i = np.append(w3i, i)                    
            if not isinstance(w4[i], float):   
                if w4[i].endswith('- s'):
                    nw4[i] = w4[i][0:-4]
                else:
                    w4i = np.append(w4i, i)
            if not isinstance(w5[i], float):   
                if w5[i].endswith('- s'):
                    nw5[i] = w5[i][0:-4]
                else:
                    w5i = np.append(w5i, i)                    

        self.df.iloc[:,11] = nw1
        self.df.iloc[:,13] = nw2
        self.df.iloc[:,15] = nw3
        self.df.iloc[:,17] = nw4
        self.df.iloc[:,19] = nw5
                        
        self.df.iloc[w1i,11] = np.nan
        self.df.iloc[w2i,13] = np.nan
        self.df.iloc[w3i,15] = np.nan
        self.df.iloc[w4i,17] = np.nan
        self.df.iloc[w5i,19] = np.nan        
        
        return self.df


    def _empty_to_nan(self):
        """Convert uncompleted workouts to np.nan's.
        
        Returns
        -------
        cfopendata : pd.Dataframe
            Crossfit open data with np.nans in uncompleted workouts.
        """
        # First week is always run otherwise file doesn't exist
        self.wodscompleted = 1
        for i, ci in enumerate([12, 14, 16, 18]):
            if self.df.iloc[0,ci] is None:
                self.df.iloc[:,[ci,ci+1]] = np.nan
            else:
                self.wodscompleted += 1
        return self
        
            
    def _height_weight_to_SI(self):
        """Convert height (feet and inches; cms) to SI units (m). and convert
        weight (lbs; kg) to SI units (kg)
        
        Returns
        -------
        cfopendata : pd.Dataframe
            Crossfit open data with height in meters.
        """
        h = self.df.iloc[:,2].values.tolist()
        w = self.df.iloc[:,3].values.tolist()
        
        nh = np.empty([len(h)], dtype=np.double)
        nw = np.empty([len(h)], dtype=np.double)
        
        for i, _tmp in enumerate(nh):
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
            if w[i].endswith('"'):
                nw[i] = round(int(w[i].split(' ')[0]) / 2.2046 )
            elif w[i].endswith('g'):
                nw[i] = round(int(w[i].split(' ')[0]))
            else:
                nw[i] = np.nan
        self.df.iloc[:,2] = nh
        self.df.iloc[:,3] = nw
        # Rename the columnc
        self.df = self.df.rename(index=str,
                                 columns={"Height": "Height (m)",
                                          "Weight": "Weight (kg)"})        
        return self.df        

    
    def _overall_percentile(self):
        """Add an overall percentile column.
        
        Returns
        -------
        cfopendata : pd.Dataframe
            Crossfit open data with add overall percentile columns.
        """         
        col = self.df['Overallrank']
        pct = np.flip(np.round(np.linspace(0, 100, num=len(self.df)),
                               decimals=4), 0)
        # Check for duplications
        pct = self._rm_dups(col, pct)
        self.df.insert(loc=10, column='Overallpercentile', value=pct)
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


    def _extract_score(self, week):
        """Convert workout score to a pd.Timedelta or integer.
        (NaNs are already in the right place).
        
        Parameters
        ----------
        week : integer
            1 to 5
        
        Returns
        -------
        cfopendata : pd.Dataframe
            Score are either a pd.Timedelta, integer or nan.
        """
        df_c_name = str(self.yearwod)+'.'+str(week)+'_score'
        s = self.df.loc[:,df_c_name].values.tolist()
       
        # Keep track of the indicies
        tdi = np.empty(shape=(0, 0), dtype=int) # time delta
        ii = np.empty(shape=(0, 0), dtype=int) # integers
        ni = np.empty(shape=(0, 0), dtype=int) # np.nans
        
        # initialize new_score array
        _s = self.df.loc[:,df_c_name].reset_index(drop=True)
        for i, _str in enumerate(s):
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
                # Convert reps to integers
                else:
                    _s[i] = int(_str.split(" ")[0])
                    ii = np.append(ii, i)
        self.df.loc[:,df_c_name] = _s.values

        self.tdi = tdi
        self.ii = ii
        self.ni = ni
        return self
    
    
    def _wod_percentile_wtd(self, week):
        """Calculate wod percentile with Timedelta.
        
        Parameters
        ----------
        week : integer
            1 to 5
        
        Returns
        -------
        cfopendata : pd.Dataframe
            Added percentile column.
        """
        # Get timedelta rows
        _s = self.df.loc[:,str(self.yearwod)+'.'+str(week)+'_score']
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
        _df_td_sorted = _s_td_sorted.to_frame(
                name = str(self.yearwod)+'.'+str(week)+'_score')
        _df_td_sorted2 = _df_td_sorted.copy()
        _df_td_sorted2 = _df_td_sorted2.rename(
                columns={str(self.yearwod)+'.'+str(week)+'_score':\
                         str(self.yearwod)+'.'+str(week)+'_percentile'})
        pct = np.transpose(np.expand_dims(pct, axis=0))
        _df_td_sorted2.loc[:] = pct
        # Put back into dataframe index
        _df_td_sorted2.index = _df_td_sorted2.index.map(int)
        _df = _df_td_sorted2.sort_index()
        pct_vals = _df.values
                
        # Insert column into self.df
        self.df.insert(loc=self.df.columns.get_loc(str(self.yearwod)+'.'+\
                                                   str(week)+'_score') + 1,
                       column=str(self.yearwod)+'.'+str(week)+'_percentile',
                       value=pct_vals)
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

 
    def _wod_percentile(self, week):
        """Calculate wod percentile for reps.
        
        Parameters
        ----------
        week : integer
            1 to 5
        
        Returns
        -------
        cfopendata : pd.Dataframe
            Added percentile column.
        """  
        _s = self.df.loc[:,str(self.yearwod)+'.'+str(week)+'_score']
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
        _df_i_sorted = _s_i_sorted.to_frame(
                name = str(self.yearwod)+'.'+str(week)+'_score')
        _df_i_sorted2 = _df_i_sorted.copy()
        _df_i_sorted2 = _df_i_sorted2.rename(
                columns={str(self.yearwod)+'.'+str(week)+'_score':\
                         str(self.yearwod)+'.'+str(week)+'_percentile'})
        pct = np.transpose(np.expand_dims(pct, axis=0))
        _df_i_sorted2.loc[:] = pct
        # Put back into dataframe index
        _df_i_sorted2.index = _df_i_sorted2.index.map(int)
        _df = _df_i_sorted2.sort_index()
        pct_vals = _df.values
 
        # Insert column into self.df
        self.df.insert(loc=self.df.columns.get_loc(str(self.yearwod)+'.'+\
                                                   str(week)+'_score') + 1,
                       column=str(self.yearwod)+'.'+str(week)+'_percentile',
                       value=pct_vals)
        return self
        return self


    def _time_to_reps(self, week, wod_type):
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
        week : integer
            1 to 5
        wod_type : string
            Contains info have the total reps and time cap
            
         Returns
        -------
        cfopendata : pd.Dataframe
            Added predicted_reps column.
        """
        
        total_reps = int(wod_type.split(' ')[0])
        time_cap = int(wod_type.split(' ')[2]) # minutes
        
        # Get timedelta rows
        _s = self.df.loc[:,str(self.yearwod)+'.'+str(week)+'_score']
        _s_td = _s[self.tdi]        
        _s_td_sorted = _s_td.sort_values()
        
        # Convert these times to reps
        p_reps = np.full_like(np.arange(len(_s_td_sorted), dtype=np.int), 0)
        counter = 0
        for i, val in _s_td_sorted.iteritems():
            reps_per_sec = val.seconds / float(total_reps)
            secs_left = (time_cap * 60) - val.seconds
            more_reps = round(secs_left / reps_per_sec)
            p_reps[counter] = total_reps + more_reps
            counter += 1
        
        # Append integer rows
        # Check if any integer rows
        if len(self.ii) > 0:
            # Get integers rowsee
            _s_i = _s[self.ii]
            _s_i_sorted = _s_i.sort_values(ascending=False)
            # Append to p_reps
            p_reps = np.append(p_reps, _s_i_sorted.values)
            # Append to s_td_sorted
            _s_td_sorted = _s_td_sorted.append(_s_i_sorted)
            
        # Append nan rows
        # Check if any nans rows
        if len(self.ni) > 0:
            # Get nan rows
            _s_n = _s[self.ni]
            # Append to s_td_sorted
            _s_td_sorted = _s_td_sorted.append(_s_n)
            # Add nans into p_reps
            _nan_arr = np.arange(len(_s_td_sorted) - len(p_reps),
                                 dtype=np.double)
            _nan_arr[:] = np.nan
            # Append NaN to pct
            p_reps = np.append(p_reps, _nan_arr)
            
        # Inser p_reps into self.df
        _df_td_sorted = _s_td_sorted.to_frame(
                name = str(self.yearwod)+'.'+str(week)+'_score')
        _df_td_sorted2 = _df_td_sorted.copy()
        _df_td_sorted2 = _df_td_sorted2.rename(
                columns={str(self.yearwod)+'.'+str(week)+'_score':\
                         str(self.yearwod)+'.'+str(week)+'_predicted_reps'})
        p_reps = np.transpose(np.expand_dims(p_reps, axis=0))
        _df_td_sorted2.loc[:] = p_reps
        # Put back into dataframe index
        _df_td_sorted2.index = _df_td_sorted2.index.map(int)
        _df = _df_td_sorted2.sort_index()
        p_reps_vals = _df.values
                
        # Insert column into self.df
        self.df.insert(loc=self.df.columns.get_loc(str(self.yearwod)+'.'+\
                                                   str(week)+'_percentile') + 1,
                       column=str(self.yearwod)+'.'+str(week)+'_predicted_reps',
                       value=p_reps_vals)
        return self
    
 
    def _reps_to_time(self, week, wod_type):
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
        week : integer
            1 to 5
        wod_type : string
            Contains info on the time cap and the total reps
            
         Returns
        -------
        cfopendata : pd.Dataframe
            Added predicted_reps column.
        """
        total_reps = int(wod_type.split(' ')[4])
        time_cap = int(wod_type.split(' ')[0]) * 60 # seconds

        # Get timedelta rows
        _s = self.df.loc[:,str(self.yearwod)+'.'+str(week)+'_score']
        _s_td = _s[self.tdi]        
        _s_td_sorted = _s_td.sort_values()

        # Get integer rows
        _s = self.df.loc[:,str(self.yearwod)+'.'+str(week)+'_score']
        _s_i = _s[self.ii]        
        _s_i_sorted = _s_i.sort_values(ascending=False)
        # Convert these reps to time
        p_time = _s_i_sorted.copy().rename(
                columns={str(self.yearwod)+'.'+str(week)+'_score':
                         str(self.yearwod)+'.'+str(week)+'_predicted_time'}).reset_index(drop=True)
        p_time.iloc[:] = 0
        counter = 0                
        for i, val in _s_i_sorted.iteritems():
            reps_per_sec = time_cap / val
            reps_left = total_reps - val
            more_time = round(reps_left * reps_per_sec)
            total_time = time_cap + more_time
            # Convert from seconds to pandas.Timedelta
            p_time.iloc[counter] = pd.to_timedelta(total_time, unit='s')
            counter += 1
            
        # Append these to original time
        p_time = _s_td_sorted.append(p_time).reset_index(drop=True)
        _s_td_sorted = _s_td_sorted.append(_s_i_sorted)
        
        # Append nan rows
        # Check if any nans rows
        if len(self.ni) > 0:
            # Get nan rows
            _s_n = _s[self.ni]
            # Append to s_td_sorted
            _s_td_sorted = _s_td_sorted.append(_s_n)
            
            # Add nans into p_time
            _nan_arr = np.arange(len(_s_td_sorted) - len(p_time),
                                 dtype=np.double)
            _nan_arr[:] = np.nan
            # Put into a Series
            _nan_s = pd.Series(_nan_arr, index=np.arange(len(_nan_arr))+len(_s_i_sorted))
            # Append NaN to p_time
            p_time = p_time.append(_nan_s).reset_index(drop=True)

        _df_td_sorted = _s_td_sorted.to_frame(
                name = str(self.yearwod)+'.'+str(week)+'_score')
        # Use index of  _df_td_sorted to sort p_time
        p_time2 = p_time.copy()
        p_time2.index = _df_td_sorted.index.map(int)
        _df = p_time2.sort_index()
        p_time_vals = _df.values

        # Inser p_time into self.df
        self.df.insert(loc=self.df.columns.get_loc(str(self.yearwod)+'.'+\
                                                   str(week)+'_percentile') + 1,
                       column=str(self.yearwod)+'.'+str(week)+'_predicted_time',
                       value=p_time_vals)
        return self