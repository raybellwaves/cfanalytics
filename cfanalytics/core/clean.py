import pandas as pd
import numpy as np

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
        
        # Check if all 5 workouts have been complete
        if self.df.iloc[0, -1] is not 0:         
            if self.scaled == 0:
                # Remove people who did not enter a single score if all 5 
                # workouts have been complete  
                self._rm_all_0s()
                # If Rx remove all who entered all scaled scores
                self._rm_all_Sc()
                # If Rx remove all who entered scaled scores and no scores
                self._rm_all_Sc_and_0s()
            else:
                # Remove all '- s' from scores
                self._rm_Sc_str()
           
        # Convert the Userid column to integers
        self.df['Userid'] = self.df.Userid.astype(int)
              
        # Convert height to SI units (m)
        self._height_to_SI()
        
        # Convert weight ti SI units (kg)
        self._weight_to_SI()
        
        # Convert the Age column to integers
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
        
        # Workouts
        for i in range(1, 6):
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
        i = 0
        while i < len(self.df):
            # Find first person with 0 entries
            if self.df.iloc[i,11] == '0' and self.df.iloc[i,13] == '0' and\
            self.df.iloc[i,15] == '0' and self.df.iloc[i,17] == '0' and\
            self.df.iloc[i,19] == '0':
                self.df = self.df.iloc[:i]
                i = i + len(self.df)
            i += 1
        return self.df.reset_index(drop=True)
    
    
    def _rm_all_Sc(self):
        """Remove people who didn't enter a Rx score in Rx division.
        
        Returns
        -------
        cfopendata : pd.Dataframe
            Crossfit open data with less rows.
        """
        for i, row in self.df.iterrows():
            # Check if last char of all scores is s
            if self.df.iloc[i,11].endswith('- s') and\
            self.df.iloc[i,13].endswith('- s') and\
            self.df.iloc[i,15].endswith('- s') and\
            self.df.iloc[i,17].endswith('- s') and\
            self.df.iloc[i,19].endswith('- s'):
                self.df.iloc[i,:] = np.nan
        # Drop rows with all NaNs
        self.df = self.df.dropna().reset_index(drop=True)
        return self.df


    def _rm_all_Sc_and_0s(self):
        """Remove people who didn't enter a Rx score in Rx division or did not 
        enter a score.
        
        Returns
        -------
        cfopendata : pd.Dataframe
            Crossfit open data with less rows.
        """
        for i, row in self.df.iterrows():
            # Check if the last char is either a 's' or a '0'
            s1 = self.df.iloc[i,11].endswith('- s') or\
            self.df.iloc[i,11] == '0'
            s2 = self.df.iloc[i,13].endswith('- s') or\
            self.df.iloc[i,13] == '0'
            s3 = self.df.iloc[i,15].endswith('- s') or\
            self.df.iloc[i,15] == '0'            
            s4 = self.df.iloc[i,17].endswith('- s') or\
            self.df.iloc[i,17] == '0'
            s5 = self.df.iloc[i,19].endswith('- s') or\
            self.df.iloc[i,19] == '0'
            if s1 and s2 and s3 and s4 and s5:
                self.df.iloc[i,:] = np.nan
        # Drop rows with all NaNs
        self.df = self.df.dropna().reset_index(drop=True)
        return self.df    

    
    def _rm_Sc_str(self):
        """Remove the ' - s' from all the scores.
        
        Returns
        -------
        cfopendata : pd.Dataframe
            Crossfit open data without ' - s' in scores.
        """
        for i, row in self.df.iterrows():
            for j, val in enumerate(np.array([11, 13, 15, 17, 19])):
                self.df.iloc[i,val] = self.df.iloc[i,val].split(' ')[0:-2]
                self.df.iloc[i,val] = " ".join(self.df.iloc[i,val])
                if not self.df.iloc[i,val]:
                    self.df.iloc[i,val] = '0'
        return self.df
            

    def _height_to_SI(self):
        """Convert height (feet and inches; cms) to SI units (m).
        
        Returns
        -------
        cfopendata : pd.Dataframe
            Crossfit open data with height in meters.
        """
        for i, row in self.df.iterrows():
            height = row['Height']
            # Check if feet (last character is "), cms (last character is s) or
            # empty
            if height.endswith('"'):
                # Add height in feet to the character(s) between ' and " 
                # (inches) and divide by 100
                new_height = round((((int(height[0]) * 12) +\
                              int(height.split('\'')[1].split('"')[0])) *\
                              2.54) / 100.0, 2)
            elif height.endswith('m'):
                new_height = int(height.split(' ')[0]) / 100.0
            else:
                new_height = np.nan
            # Could clean this up and check for physical values > 0.3 m and < 
            # 2.2 m
            self.df.loc[i, 'Height'] = new_height
        # Rename the column
        self.df = self.df.rename(index=str,
                                 columns={"Height": "Height (m)"})
        return self.df
    
    
    def _weight_to_SI(self):
        """Convert weight (feet and inches; cms) to SI units (m).
        
        Returns
        -------
        cfopendata : pd.Dataframe
            Crossfit open data with height in meters.
        """        
        for i, row in self.df.iterrows():
            weight = row['Weight']
            if weight.endswith('b'):
                new_weight = round(int(weight.split(' ')[0]) / 2.2046 )
            elif weight.endswith('g'):
                new_weight = round(int(weight.split(' ')[0]))
            else:
                new_weight = np.nan
            self.df.loc[i, 'Weight'] = new_weight
        # Rename the column
        self.df = self.df.rename(index=str,
                                 columns={"Weight": "Weight (kg)"})
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
        # Keep track of the indicies
        tdi = np.empty(shape=(0, 0)) # time delta
        ii = np.empty(shape=(0, 0)) # integers
        ni = np.empty(shape=(0, 0)) # np.nans
        for i, row in self.df.iterrows():
            score = row[df_c_name]
            # Remove any scaled scores if Rx
            if self.scaled == 0:
                # Remove any scled scores
                if score.endswith('- s'):
                    new_score = np.nan
                    ni = np.append(ni, i)
                else:
                    if ':' in score:
                        # Some team scores are H:MM:SS
                        if score.count(':') > 1:
                            new_score = pd.to_timedelta(score)
                        else:
                            new_score = pd.to_timedelta('0:'+score)
                        tdi = np.append(tdi, i)
                    elif 's' in score:
                        new_score = int(score.split(" ")[0])
                        ii = np.append(ii, i)
                    else:
                        new_score = np.nan
                        ni = np.append(ni, i)
            else:
                # Should write this as a function rather than copying above...
                if ':' in score:
                    new_score = pd.to_timedelta('0:'+score)
                    tdi = np.append(tdi, i)
                elif 's' in score:
                    new_score = int(score.split(" ")[0])
                    ii = np.append(ii, i)
                else:
                    new_score = np.nan
                    ni = np.append(ni, i)
            self.df.loc[i, df_c_name] = new_score
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