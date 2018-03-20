import requests # HTTP library
import asyncio # Asynchronous I/O
from aiohttp import ClientSession # Asynchronous HTTP Client/Server


import pandas as pd
import numpy as np


import os
import time
import shutil


class Affiliatelist(object):
    """An object to download CrossFit affiliate information.
    """
    
    def __init__(self, path):
        """Crossfit affiliate data object.
        
        Parameters
        ----------
        path : str
            Directory where to save data.        

        Returns
        -------
        affiliatelist : pd.Dataframe
            Affiliate data.
            
        Example
        -------
        cfa.Affiliatelist('Data/')
        """
        # Setup the name of the file to save
        self.dname = 'Affiliate_list'
        self.path = path
        # Setup a directory to store the temporary files
        path2 = self.path+'/ind_files'
        self.path2 = path2
        if not os.path.isdir(path2):
            os.makedirs(path2)

        self.basepath = 'https://map.crossfit.com'
        self.headers = {'Host': 'map.crossfit.com',
               'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2'+\
               ') AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.13'+\
               '2 Safari/537.36'}
        
        # Setup DataFrame
        self.columns = ['Affiliate_id', 'Affiliate_name', 'Address', 'City',
                        'State', 'Zip', 'Country', 'Website', 'Phone']
        self.data = pd.DataFrame(columns=self.columns)
        empty_df = pd.DataFrame(columns=self.columns) # Initiallized DataFrame
        
        # See https://map.crossfit.com/getAllAffiliates.php for a full list
        # of affiliate information. Column 3 is the Affiliate id
        self.startpage = 3 # First Affiliate id
        self.aidcount = self.startpage
        self.endpage = 21363 # Last Affiliate id
        self.npages = self.endpage - self.startpage + 1
        self.batchpages = 100
        
        ii = self.startpage
        while ii <= int(self.npages/self.batchpages):
            print('getting aids '+str(self.startpage)+'-'+str(self.startpage+\
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
            self._save_df(ii, empty_df)
            
        # Append all data files
        for root, dirs, files in os.walk(path2):
            for file_ in files:
                _df = pd.read_pickle(os.path.join(root, file_))
                self.data = self.data.append(_df).reset_index(drop=True)
                
        self.data = self.data.sort_values(by=['Affiliate_id']) 
        self.data = self.data.reset_index(drop=True)
        
        # Add latitude and longitude data
        self._add_lat_lon()
                
        self.data.to_pickle(self.path+'/'+self.dname)
        self.data.to_csv(path_or_buf=self.path+'/'+self.dname+'.csv')
        
        # Remove all files in ddii2
        shutil.rmtree(self.path2)
        
        
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
                self.params={"aid": self.p}
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
        async with session.get(self.basepath+'/getAffiliateInfo',
                               params=self.params,
                               headers=self.headers) as response: 
            out = await response.json(content_type='text/html')
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
        aid = self.aidcount
        name = response['name']
        if name is not None:
            ad = response['address']
            c = response['city']
            s = response['state']  
            z = response['zip']  
            co = response['country']  
            w = response['website']
            ph = response['phone']
            row = [[aid, name, ad, c, s, z, co, w, ph]]
            df = pd.DataFrame(row, columns=self.columns)
            self.data = self.data.append(df)
        self.aidcount += 1
        
        
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
        self.dname_tmp = 'Affiliate_list'+str(ii).zfill(5)
        self.data_tmp.to_pickle(self.path2+'/'+self.dname_tmp)
        self.data = empty_df
        return self
    
    
    def _add_lat_lon(self):
        """Add latitude and longitude to the Affiliate list data.
        
        Returns
        -------
        data : pd.Dateframe
            Adds a latitude and longitude colomn
        """
        self.data["Latitude"] = ""
        self.data["Longitude"] = ""
        
        response = requests.get(self.basepath+'/getAllAffiliates.php').json()
        r = np.array(response)
        ids_with_lat_lon = r[:,3].astype(int)
        lats = r[:,0].astype(np.float64)
        lons = r[:,1].astype(np.float64)
        
        ids = self.data['Affiliate_id'].values.astype(int)
        # Find ids in ids_with_lat_lon
        ix = np.where(np.in1d(ids_with_lat_lon, ids))[0]
        sub_ids_with_lat_lon = ids_with_lat_lon[ix]
        sub_lats = lats[ix]
        sub_lons = lons[ix]        

        datatmp = self.data.set_index('Affiliate_id')
        datatmp.loc[sub_ids_with_lat_lon,'Latitude'] = sub_lats
        datatmp.loc[sub_ids_with_lat_lon,'Longitude'] = sub_lons
        self.data["Latitude"] = datatmp["Latitude"].values
        self.data["Longitude"] = datatmp["Longitude"].values
        return self