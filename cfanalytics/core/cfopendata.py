import requests # HTTP library
import asyncio # Asynchronous I/O
from aiohttp import ClientSession # Asynchronous HTTP Client/Server


import pandas as pd


import os
import time
import shutil


from .utils import open_wods


class Cfopendata(object):
    """An object to download CrossFit open data.
    """
    
    
    def __init__(self, year, division, scaled, path):
        """Crossfit open data object.
        
        Parameters
        ----------
        year : int
            Year to download crossfit data e.g. 2017.
        division : int (1-19)
            Numerical values of the division.
            1 : Men
            2 : Women
            3 : Men 45-49
            4 : Women 45-49
            5 : Men 50-54
            6 :Women 50-54
            7 : Men 55-59
            8 : Women 55-59
            9 : Men 60+
            10 : Women 60+
            11 : Team
            12 : Men 40-44
            13 : Women 40-44
            14 : Boys 14-15
            15 : Girls 14-15
            16 : Boys 16-17
            17 : Girls 16-17
            18 : Men 35-39
            19 : Women 35-39            
        scaled : int (0,1)
            Numerical values if workout was Scaled or RX'd.
            0 : Rx
            1 : Sc
        path : str
            Directory where to save data.

        Returns
        -------
        cfopendata : pd.Dataframe
            Crossfit open data.
            
        Example
        -------
        cfa.Cfopendata(2018, 1, 0, 'Data/')
        """

        self.year = year
        if self.year < 2017:
            raise ValueError('This is only tested on 2017 and 2018')
        self.division = division
        self.scaled = scaled
        self.path = path
        
        # Setup a directory to store the temporary files
        path2 = self.path+'/ind_files'
        self.path2 = path2
        if not os.path.isdir(path2):
            os.makedirs(path2)
        
        # Setup the name of the file to save
        self.dname = self._div_to_name()+'_'+self._scaled_to_name()+'_'+\
                     str(self.year)+'_raw'
                     
        self.basepath = 'https://games.crossfit.com/competitions/api/v1/comp'+\
                        'etitions/open/'+str(self.year)+'/leaderboards?'
                        
        self.headers = {'Host': 'games.crossfit.com',
               'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2'+\
               ') AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.13'+\
               '2 Safari/537.36'}
                        
        # Setup DataFrame
        wod_info = open_wods(self.year)
        self.wodscompleted = int(wod_info['wodscompleted'].values)
        score_cols = wod_info['dfheader'].values
        self.columns = ['User_id', 'Name', 'Height', 'Weight', 'Age',
                        'Region_id', 'Region_name', 'Affiliate_id',
                        'Overall_rank', 'Overall_score']
        self.columns.extend(score_cols)
        self.data = pd.DataFrame(columns=self.columns)
        empty_df = pd.DataFrame(columns=self.columns) # Initiallized DataFrame

        print('Downloading '+str(self.dname))
        
        # Find out how pages of results there are
        self.npages = self._get_npages()
        
        # Workout how many pages to get at once based on the number of pages
        if self.npages < 10:
            self.batchpages = 2
        elif self.npages >= 10 and self.npages < 100:
            self.batchpages = 10
        else:
            self.batchpages = 30
            
        # Loop over the batch pages
        self.startpage = 1
        ii = 1
        while ii <= int(self.npages/self.batchpages):
            print('getting pages '+str(self.startpage)+'-'+str(self.startpage+\
                  self.batchpages-1)+' of '+str(self.npages)) 

            start_time = time.time()
            self._ailoop()
            print("that took " +\
                  str(round((time.time() - start_time) / 60.0, 2)) +\
                  " minutes")

            # Save data after each _ailoop is called
            self._save_df(ii, empty_df)
                            
            ii += 1
            self.startpage = self.startpage + self.batchpages
            
        # Check if any pages left
        if self.startpage <= self.npages:
            # Update batchpages to however many pages are left     
            self.batchpages = self.npages - self.startpage + 1
            print('getting pages '+str(self.startpage)+'-'+str(self.startpage+\
                  self.batchpages-1)+' of '+str(self.npages))
            start_time = time.time() # Start time
            self._ailoop()
            print("that took " +\
                  str(round((time.time() - start_time) / 60.0, 2)) +\
                  " minutes")
            
            # Save data after each _ailoop is called
            self._save_df(ii, empty_df)                
            
        # Append all data files
        for root, dirs, files in os.walk(path2):
            for file_ in files:
                _df = pd.read_pickle(os.path.join(root, file_))
                self.data = self.data.append(_df).reset_index(drop=True)
                
        # For unknown reasons it puts the batch pages ~100 onwards at the start
        # Sort data by 'Overallrank' coloumn
        self.data['Overall_rank'] = self.data['Overall_rank'].astype(int)
        self.data = self.data.sort_values(by=['Overall_rank'])        
        # This doesn't quite match the leaderboard but it shouldn't matter
        # As everyone who is ranked the same overall will have similar stats
        self.data['Overall_rank'] = self.data['Overall_rank'].astype(str)
        self.data = self.data.reset_index(drop=True)
        self.data.to_pickle(self.path+'/'+self.dname)
        self.data.to_csv(path_or_buf=self.path+'/'+self.dname+'.csv')
        
        # Remove all files in ddii2
        shutil.rmtree(self.path2)
        

    def _div_to_name(self):
        """Division number to a string.
    
        Returns
        -------
        out : string
            Name of the division.    
        """
        div_dict = {'1':"Men",
                    '2':"Women",
                    '3':"Men_45-49",
                    '4':"Women_45-49",
                    '5':"Men_50-54",
                    '6':"Women_50-54",
                    '7':"Men_55-59",
                    '8':"Women_55-59",
                    '9':"Men_60+",
                    '10':"Women_60+",
                    '11':"Team",
                    '12':"Men_40-44",
                    '13':"Women_40-44",
                    '14':"Boys_14-15",
                    '15':"Girls_14-15",
                    '16':"Boys_16-17",
                    '17':"Girls_16-17",
                    '18':"Men_35-39",
                    '19':"Women_35-39"}
        return div_dict[str(self.division)]


    def _scaled_to_name(self):
        """Scaled number to a string.
    
    
        Returns
        -------
        out : string
            Workout type.
    
        """
        wt_list = ['Rx','Sc']
        return wt_list[self.scaled]


    def _get_npages(self):
        """Get the number of pages of results.
        
        Returns
        -------
        npages : int
           Number of pages.
        """
        response = requests.get(self.basepath,
                                params={"division": self.division,
                                        "scaled": self.scaled,
                                        "sort": "0",
                                        "fittest": "1",
                                        "fittest1": "0",
                                        "occupation": "0",
                                        "competition": "1",
                                        "page": 1},
                                        headers=self.headers).json()
        if self.year == 2018:
            return  response['pagination']['totalPages']
        else:
            return response['totalpages']
        

    def _ailoop(self):
        """Create a concurrent loop.
        
        See https://www.blog.pythonlibrar\y.org/2016/07/26/python-3-an-intro\
        -to-asyncio/
        """
        aioloop = asyncio.get_event_loop()
        aifuture = asyncio.ensure_future(self._loop_pages())
        aioloop.run_until_complete(aifuture)
        

    async def _loop_pages(self):
        """async function that creates semaphores and does http requests
        by a segmented number of pages.
        
        Returns
        -------
        Calls ._download_page()
        Calls ._get_data()
        """
        async_list = []
        sem = asyncio.Semaphore(self.batchpages) # create asyncio.locks.Semaph\
        #ore object
        async with ClientSession() as session:
            for p in range(self.startpage, self.startpage+self.batchpages):
                self.p = p
                self.params={"division": self.division,
                             "scaled": self.scaled,
                             "sort": "0",
                             "fittest": "1",
                             "fittest1": "0",
                             "occupation": "0",
                             "competition": "1",
                             "page": self.p}
                task = asyncio.ensure_future(self._download_page(sem, session))            
                async_list.append(task)
                results = await asyncio.gather(*async_list)

        # Loop through the batch pages    
        for page in results:
            self._get_data(page)     


    async def _download_page(self, sem, session):
        """ async function that checks semaphore unlocked before calling the
        get function.
        
        Parameters
        ----------
        sem : int
            Semaphore.
        session : aiohttp.client.ClientSession  
        
        Returns
        -------
        Calls ._get_page
        """
        async with sem:
            return await self._get_page(session)

        
    async def _get_page(self, session):
        """ async function that makes HTTP GET requests.
    

        Parameters
        ----------
        session : aiohttp.client.ClientSession 
        
        Returns
        -------        
        out : JSON response object.
        """
        async with session.get(self.basepath, params=self.params,
                               headers=self.headers) as response: 
            out = await response.json()
            return out

        
    def _get_data(self, response):
        """Get data from response.
        
        Parameters
        ----------
        response : dict
            Response.

        Returns
        -------
        data : pd.Dateframe
            Append data to self.data.
        """
        wr = [None] * self.wodscompleted
        ws = [None] * self.wodscompleted
        
        if self.year == 2018:
            athletes = response['leaderboardRows']
            nathletes = len(athletes)
            
             # Loop over athletes in the page
            for i in range(nathletes):
                athlete = athletes[i]
                _id = athlete['entrant']['competitorId']
                name = athlete['entrant']['competitorName']
                height = athlete['entrant']['height']
                weight = athlete['entrant']['weight']
                age = athlete['entrant']['age']
                ri = athlete['entrant']['regionId']
                rn = athlete['entrant']['regionName']
                ai = athlete['entrant']['affiliateId']
                _or = athlete['overallRank']
                _os = athlete['overallScore']
                row = [_id, name, height, weight, age, ri, rn, ai, _or, _os]
                
                # Loop over workouts
                for j in range(self.wodscompleted):
                    wr[j] = athlete['scores'][j]['rank']
                    row.append(wr[j])
                    ws[j] = athlete['scores'][j]['scoreDisplay']
                    row.append(ws[j])
                row = [row]
                df = pd.DataFrame(row, columns=self.columns)
                self.data = self.data.append(df)
        else:
            athletes = response['athletes']
            nathletes = len(athletes)
            
            # Loop over athletes in the page
            for i in range(nathletes):
                athlete = athletes[i]
                _id = athlete['userid']
                name = athlete['name']
                height = athlete['height']
                weight = athlete['weight']
                age = athlete['age']
                ri = athlete['regionid']
                rn = athlete['region']
                ai = athlete['affiliateid']
                _or = athlete['overallrank']
                _os = athlete['overallscore']
                row = [_id, name, height, weight, age, ri, rn, ai, _or, _os]
                
                # Loop over workouts
                for j in range(self.wodscompleted):
                    wr[j] = athlete['scores'][j]['workoutrank']
                    row.append(wr[j])
                    ws[j] = athlete['scores'][j]['scoredisplay']
                    row.append(ws[j])
                row = [row]
                df = pd.DataFrame(row, columns=self.columns)
                self.data = self.data.append(df)

            
    def _save_df(self, ii, empty_df):
        """Save pandas.DataFrame.
        
        Parameters
        ----------
        ii : int
            Batchpages counter.
        empty_df : pd.DataFrame.
            Empty pandas DataFrame with coloumns already added.

        Returns
        -------
        data : pd.Dateframe
            Saves file and make self.data empty
        """
        self.data_tmp = self.data.reset_index(drop=True)
        self.dname_tmp = self._div_to_name()+'_'+self._scaled_to_name()+'_'+\
            str(self.year)+'_raw_'+str(ii).zfill(4)
        self.data_tmp.to_pickle(self.path2+'/'+self.dname_tmp)
        self.data = empty_df
        return self