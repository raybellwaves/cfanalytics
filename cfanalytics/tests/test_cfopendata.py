import requests # HTTP library
import asyncio # Asynchronous I/O
from aiohttp import ClientSession # Asynchronous HTTP Client/Server


import pandas as pd
import sys
import pytest


class TestCfopendata(TestCase):    
    def test_cfopendata(self):
        self.year = 2017
        self.division = 1
        self.scaled = 0
        self.batchpages = 10
        
        self.basepath = 'https://games.crossfit.com/competitions/api/v1/comp'+\
                        'etitions/open/'+str(self.year)+'/leaderboards?'
                        
        self.headers = {'Host': 'games.crossfit.com',
               'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2'+\
               ') AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.13'+\
               '2 Safari/537.36'}
                        
        # Setup DataFrame
        self.columns = ['Userid', 'Name', 'Height', 'Weight', 'Age', 'Regionid',
                   'Regionname', 'Affiliateid', 'Overallrank', 'Overallscore', 
                   str(self.year)[2:]+'.1_rank', str(self.year)[2:]+'.1_score',
                   str(self.year)[2:]+'.2_rank', str(self.year)[2:]+'.2_score',
                   str(self.year)[2:]+'.3_rank', str(self.year)[2:]+'.3_score',
                   str(self.year)[2:]+'.4_rank', str(self.year)[2:]+'.4_score',
                   str(self.year)[2:]+'.5_rank', str(self.year)[2:]+'.5_score']
        self.data = pd.DataFrame(columns=self.columns)
        
        # Find out how pages of results there are
        self.npages = 10
        
        if self.batchpages > self.npages:
            print('batchpages must be less than number of pages.')
            raise ValueError('Number of pages for year: '+str(self.year)+', '+\
                             'division: '+str(self.division)+', scaled: '+\
                             str(self.scaled)+'is '+str(self.npages)+'. '+\
                             'bactchpages is '+str(self.batchpages)+'.')
        
        # Loop over the batch pages
        ii = 0
        self.startpage = 1
        while ii < int(self.npages/self.batchpages):
            self._ailoop()
            ii += 1
            self.startpage = self.startpage + self.batchpages

        # Check that the winner is Matt Fraser
        expected = 'Mathew Fraser'
        actual = self.data.iloc[0][1]
        print(expected)
        print(actual)
        sys.exit()           
        assert expected == actual
        
        
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
            # Loop over workout
            wr = [None] * 5
            ws = [None] * 5
            for j in range(5):                    
                wr[j] = athlete['scores'][j]['workoutrank']
                ws[j] = athlete['scores'][j]['scoredisplay']
            row = [[_id, name, height, weight, age, ri, rn, ai, _or, _os,
                    wr[0], ws[0], wr[1], ws[1], wr[2], ws[2], wr[3], ws[3],
                    wr[4], ws[4]]]
            df = pd.DataFrame(row, columns=self.columns)
            self.data = self.data.append(df)

            
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
                    '17':"Girls_16-17"}
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