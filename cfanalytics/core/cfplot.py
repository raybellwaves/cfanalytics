import pandas as pd
import xarray as xr
import numpy as np


import cartopy.feature as cfeature
import cartopy.crs as ccrs
import cartopy.io.shapereader as shapereader
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from salem import GoogleVisibleMap, Map


import math
import os


class Cfplot(object):
    """An object to plot downloaded CrossFit open data.
    """
    
    def __init__(self, path):
        """Plot Crossfit open data object.
        
        Parameters
        ----------
        path : string
            File path.
            
        Returns
        -------
        matplotlib.pyplot.figure : matplotlib.pyplot.figure
            Creates Crossfit plot.
        """
        self.path = path
        self.df = pd.read_pickle(self.path)
        self.year = int(str(self.path[-4:]))
        if int(self.year) < 2018:
            raise ValueError('This is only tested on 2018')
        # Check you can read in the Affiliate_list
        self._dir = '/'+'/'.join(self.path.split('/')[1:-1])+'/'
        # Create a Plot directory
        self.plotdir = '/'+'/'.join(self.path.split('/')[1:-2])+'/'+'Plots/'
        if not os.path.isdir(self.plotdir):
            os.makedirs(self.plotdir)        
        self.fname = self.path.split('/')[-1]        

        
    def regionplot(self, column=None, how=None):
        """Create a plot showing a map of the world with data averaged in
        regions.
        https://games.crossfit.com/article/change-coming-2018-season/liftoff
        The regioins are given here:
        https://games-support.crossfit.com/article/100-what-are-the-boundaries\
        -of-the-crossfit-games-regions-what-states-countries-are-included-in-\
        each
        There are 18 regions:
        5 : Canada West (Yukon, Northwest Territories, Nunavut,
        British Columbia, Alberta, Saskatchewan, Manitoba)
        6 : Central East (Michigan, Ohio, Tennessee, Kentucky, Indiana)        
        9 : Mid Atlantic (Pennsylvania, Maryland, Delaware, West Virginia,
        Virginia, North Carolina)
        10 : North Central (North Dakota, South Dakota, Illinois, Kansas,
        Oklahoma, Nebraska, Minnesota, Arkansas, Missouri, Iowa, and Wisconsin)
        11 : North East (Massachusetts, Maine, Vermont, New Hampshire,
        Connecticut, Rhode Island, New York, New Jersey)
        14 : South Central (Texas, Louisiana, Mississippi)
        15 : South East (Alabama, Georgia, South Carolina, Florida)
        17 : South West (Utah, Nevada, Arizona, New Mexico, Colorado)
        18 : Canada East (Ontario, Quebec, Newfoundland and Labrador,
        New Brunswick, Prince Edward Island, Nova Scotia)
        19 : West Coast (California, Oregon, Washington, Hawaii, Wyoming,
        Idaho, Alaska, and Montana)
        20 : Asia (Russia east of the Ural Mountains and all Asian countries
        east of the Caspian Sea.)
        21 : Australasia (Australia, New Zealand, Papua New Guinea, Antarctica,
        and some Pacific Islands)
        22 : Europe North (Aland Islands, Bulgaria, Belarus, Bouvet Island,
        Czech Republic, Denmark, Estonia, Finland, Faroe Islands, Greenland,
        Hungary, Iceland, Lithuania, Latvia, Norway, Poland, Romania,
        Svalbard and Jan Mayen, Slovakia, Sweden, Ukraine,
        and part of Russia west of the Ural Mountains.)
        23 : Europe Central (Albania, Austria, Belgium, Bosnia and Herzegovina,
        Germany, United Kingdom, Greece, Croatia, Isle of Man, Ireland,
        Liechtenstein, Luxembourg, Moldova, Macedonia, Netherlands, Serbia,
        Slovenia and Kosovo)
        24 : Europe South (SAndorra, Switzerland, Cyprus, Spain, France,
        Guernsey, Gibraltar, Italy, Jersey, Monaco, Malta, Montenegro,
        Portugal, San Marino, Turkey and Holy See (Vatican))
        25 : Africa Middle East (Africa plus the Middle East)
        26 : Central America (Mexico through Panama and the islands to the
        east)
        27 : South America (Countries south of Panama)
        
        Parameters
        ----------
        column : string
            Name of column in the file.
            Must be X_rank.
        how : string
            Name of method to analyze the data.
            P0.01 : 0.01th percentile.
            
        Returns
        -------
        matplotlib.pyplot.figure : matplotlib.pyplot.figure
            Creates regional plot.
            
        Example
        -------
        cfa.Cfplot('Men_Rx_2018').regionplot(column='Overall_rank', how='P5')
        """            
        # If column and how are not provided use 'Overall_rank' and 'P5'
        if column is None:
            self.column = 'Overall_rank'
        else:
            self.column = column
        if how is None:
            self.how = 'P5'
        else:
            self.how = how
            
        # Make sure a X_rank column was entered
        if self.column.split('_')[-1] != 'rank':
            raise ValueError('column should be a rank column')
            
        #Obtain region names
        self._region_names()
                
        # Create xr.DataArray to store the data
        da = xr.DataArray(np.full((len(self.reg_dict.keys()), len(self.df)),
                                  np.nan, dtype=np.double),
            coords=[list(self.reg_dict.values()), np.arange(len(self.df))],
            dims=['regions','athletes'])
        # Fill with data from each region
        for i, reg_id in enumerate(self.reg_dict.keys()):
            reg_name = self.reg_dict[reg_id]
            df = self.df.query('Region_id == '+str(reg_id))
            da.loc[reg_name, 0:len(df[self.column].values)-1] =\
            df[self.column].values
            
        # Create xr.Dataset to store the analysis with the number of athletes
        _da = da[:,0]
        _da[:] = np.nan
        ds = xr.Dataset({'natheltes':_da, self.how:_da}).drop('athletes')
        
        # Count athletes        
        ds['natheltes'].values = np.count_nonzero(~np.isnan(da.values), axis=1)

        # Data analysis method        
        if self.how[0] == 'P':
            # Percentile method
            percentile_val = float(self.how.split('P')[-1])/100.
            ds[self.how].values = \
            da.quantile(percentile_val, dim='athletes').astype(int)
            
        # Print the data
        self._show_data(ds)

        # Plot the data
        self._plot_regs()        

        
    def _region_names(self):
        """Return a dictionary of region names.
            
        Returns
        -------
        self.reg_dict : dict
            Region id's and names.
        """
        self.reg_dict = {5:"Canada_West",
                         6:"Central_East",
                         9:"Mid_Atlantic",
                         10:"North_Central",
                         11:"North_East",
                         14:"South_Central",
                         15:"South_East",
                         17:"South_West",
                         18:"Canada_East",
                         19:"West_Coast",
                         20:"Asia",
                         21:"Australasia",
                         22:"Europe_North",
                         24:"Europe_South",
                         23:"Europe_Central",
                         25:"Africa_Middle_East",
                         26:"Central_America",
                         27:"South_America"}
        return self
    
    
    def _show_data(self, ds):
        """Print the data.
        
        Parameters
        ----------
        ds : xr.Dataset
            xr.Dataset with natheltes and analysis results and
            Coordinates: regions.
            
        Returns
        -------
        sorted : xr.Dataset
            Sorted dataset.
        """
        ds_sorted = ds.sortby(ds[self.how])
        print('Printing results for...')
        print(self.fname)        
        print(self.column)
        print('rank, region, nathletes, '+self.how)
        for i in range(0, len(ds_sorted.coords['regions'])):
            print(i+1,',',ds_sorted.coords['regions'].values[i],',',
                  ds_sorted['natheltes'].values[i],',',
                  round(ds_sorted[self.how].values[i],1))
        self.ds_sorted = ds_sorted
        print('')
        print('Printing results in reddit table format...')
        print('Rank | Region | Number of athletes in region | '+\
              self.column+ ' '+self.how)
        print('---- | ------ | ---------------------------- | --------------')
        for i in range(0, len(ds_sorted.coords['regions'])):
            print(str(i+1)+' | '+ds_sorted.coords['regions'].values[i]+' | '+\
                  str(ds_sorted['natheltes'].values[i])+' | '+\
                  str(round(ds_sorted[self.how].values[i],1)))
        print('')
        _tmp = ds.sortby('natheltes')
        print('Printing results in order of region size...')
        print('rank, region, nathletes, '+self.how)
        for i in range(0, len(_tmp.coords['regions'])):
            print(i+1,',',_tmp.coords['regions'].values[i],',',
                  _tmp['natheltes'].values[i],',',
                  round(_tmp[self.how].values[i],1))        
        return self
        

    def _plot_regs(self):
        """Plot the regional analysis.
        
        Parameters
        ----------
        self.ds_sorted : xr.Dataset
            1D xr.DataArray with Coordinates: regions.
            
        Returns
        -------
        matplotlib.pyplot.figure : matplotlib.pyplot.figure
            Creates Crossfit plot.        
        """
        # Create a color array of size len(regions)
        # Could add colortype as input
        self.colors = cm.nipy_spectral(np.linspace(0,1,
            len(self.ds_sorted.coords['regions'])))
        
        # Setup plot
        plt.figure(figsize=(18, 9))
        self.ax = plt.axes(projection=ccrs.PlateCarree())
        self.ax.set_global()
        self.ax.stock_img()

        # Loop over regions and plot polygon and text
        for i in range(0, len(self.ds_sorted.coords['regions'])):
            reg_name = self.ds_sorted.coords['regions'].values[i]
            self.regcount = i
            
            # Obtain rank
            self._rank()
            
            # Initialize geometries
            self.geoms = []
            if reg_name == 'Canada_West':
                self._plot_cw()
            elif reg_name == 'Central_East':
                self._plot_cene()
            elif reg_name == 'Mid_Atlantic':
                self._plot_ma()
            elif reg_name == 'North_Central':
                self._plot_nc()
            elif reg_name == 'North_East':
                self._plot_ne()
            elif reg_name == 'South_Central':
                self._plot_sc()
            elif reg_name == 'South_East':
                self._plot_se()
            elif reg_name == 'South_West':
                self._plot_sw()
            elif reg_name == 'Canada_East':
                self._plot_ce()
            elif reg_name == 'West_Coast':
                self._plot_wc()
            elif reg_name == 'Asia':
                self._plot_a()
            elif reg_name == 'Australasia':
                self._plot_aa()
            elif reg_name == 'Europe_North':
                self._plot_en()
            elif reg_name == 'Europe_South':
                self._plot_es()
            elif reg_name == 'Europe_Central':
                self._plot_ec()
            elif reg_name == 'Africa_Middle_East':
                self._plot_ame()
            elif reg_name == 'Central_America':
                self._plot_ca()
            else:
                # South_America
                self._plot_sa()
                
            # Plot polygon
            self.ax.add_feature(cfeature.ShapelyFeature(self.geoms,
                                                        ccrs.PlateCarree()),
                facecolor=self.colors[self.regcount])

            # Create string to plot over polygon
            self.reg_plot_str = self.rank+'('+\
            str(self.ds_sorted[self.how].values[i])+')'
                
            # Plot results on top of polygon
            plt.text(self.lonloc, self.latloc, self.reg_plot_str,
                     color=self.strcol, fontsize=10, weight='bold',
                     transform=ccrs.PlateCarree())

        self.ax.coastlines(resolution='10m')
        plt.title(self.fname+' | '+self.column+' | '+self.how)
        plt.savefig(self.plotdir+self.fname+'_'+self.column+'_'+self.how+\
                    '.png', bbox_inches = 'tight')
        # Full res figure but huge (Mb's)
        #plt.savefig(self.plotdir+self.fname+'_'+self.column+'_'+self.how+\
        #            '.png', bbox_inches = 'tight', format='eps')        
        plt.show()


    def _rank(self):
        """Obtain rank of region in format for matplotlib.
        
        Parameters
        ----------
        self.regcount : int
            
        Returns
        -------
        self.rank : str       
        """
        x = self.regcount+1
        ordinal = lambda x: "%d%s" %\
        (x,"tsnrhtdd"[(math.floor(x/10)%10!=1)*(x%10<4)*x%10::4])
        _o = ordinal(x)
        # Remove the number from the string
        _o = _o.replace(str(x), "")
        self.rank = str(x)+'$^{'+_o+'}$'
        return self


    def _plot_cw(self):
        """Get Canada West plotting info.
        
        Returns
        -------
        self
            Adds attributes used for plotting
        """
        self.loc_names = ['Yukon','Northwest Territories','Nunavut',
                          'British Columbia','Alberta','Saskatchewan',
                          'Manitoba']
        # Get geometries
        self._get_geoms('admin_1_states_provinces_shp', 'name')
        
        # Workout string color
        self._get_str_col()
        
        # Longitude and latitude location of text
        self.lonloc = -130
        self.latloc = 60
        return self
        
        
    def _plot_cene(self):
        """Get Central East plotting info.
        
        Returns
        -------
        self
            Adds attributes used for plotting
        """
        # Add region infront of self.rank
        self.rank = 'CE: '+self.rank
        
        self.loc_names = ['Michigan','Ohio','Tennessee','Kentucky','Indiana']
        # Get geometries
        self._get_geoms('admin_1_states_provinces_shp', 'name')        

        self.strcol = 'black'
        
        # Latitude and longitude location of text
        self.lonloc = -65
        self.latloc = 30
        return self


    def _plot_ma(self):
        """Get Mid Atlantic plotting info.
        
        Returns
        -------
        self
            Adds attributes used for plotting
        """
        # Add region infront of self.rank
        self.rank = 'MA: '+self.rank
        
        self.loc_names = ['Pennsylvania','Maryland','Delaware','West Virginia',
                          'Virginia','North Carolina']
        # Get geometries
        self._get_geoms('admin_1_states_provinces_shp', 'name')

        self.strcol = 'black'
        
        # Latitude and longitude location of text
        self.lonloc = -65
        self.latloc = 25
        return self
        
        
    def _plot_nc(self):
        """Get North Central plotting info.
        
        Returns
        -------
        self
            Adds attributes used for plotting
        """
        # Add region infront of self.rank
        self.rank = 'NC: '+self.rank
        
        self.loc_names = ['North Dakota','South Dakota','Illinois','Kansas',
                          'Oklahoma','Nebraska','Minnesota','Arkansas',
                          'Missouri','Iowa','Wisconsin']
        # Get geometries
        self._get_geoms('admin_1_states_provinces_shp', 'name')

        self.strcol = 'black'
        
        # Latitude and longitude location of text
        self.lonloc = -65
        self.latloc = 35
        return self
        
        
    def _plot_ne(self):
        """Get North East plotting info.
        
        Returns
        -------
        self
            Adds attributes used for plotting
        """
        # Add region infront of self.rank
        self.rank = 'NE: '+self.rank
        
        self.loc_names = ['Massachusetts','Maine','Vermont','New Hampshire',
                          'Connecticut','Rhode Island','New York','New Jersey']
        # Get geometries
        self._get_geoms('admin_1_states_provinces_shp', 'name')
        
        self.strcol = 'black'
        
        # Latitude and longitude location of text
        self.lonloc = -65
        self.latloc = 40
        return self

        
    def _plot_sc(self):
        """Get South Central plotting info.
        
        Returns
        -------
        self
            Adds attributes used for plotting
        """
        # Add region infront of self.rank
        self.rank = 'SC: '+self.rank
        
        self.loc_names = ['Texas','Louisiana','Mississippi']
        # Get geometries
        self._get_geoms('admin_1_states_provinces_shp', 'name')        

        self.strcol = 'black'
        
        # Latitude and longitude location of text
        self.lonloc = -155
        self.latloc = 30
        return self
        
        
    def _plot_se(self):
        """Get South East plotting info.
        
        Returns
        -------
        self
            Adds attributes used for plotting
        """
        # Add region infront of self.rank
        self.rank = 'SE: '+self.rank
        
        self.loc_names = ['Alabama','Georgia','South Carolina','Florida']
        # Get geometries
        self._get_geoms('admin_1_states_provinces_shp', 'name')        

        self.strcol = 'black'
        
        # Latitude and longitude location of text
        self.lonloc = -65
        self.latloc = 20
        return self 


    def _plot_sw(self):
        """Get South West plotting info.
        
        Returns
        -------
        self
            Adds attributes used for plotting
        """
        # Add region infront of self.rank
        self.rank = 'SW: '+self.rank
        
        self.loc_names = ['Utah','Nevada','Arizona','New Mexico','Colorado']
        # Get geometries
        self._get_geoms('admin_1_states_provinces_shp', 'name')        

        self.strcol = 'black'
        
        # Latitude and longitude location of text
        self.lonloc = -155
        self.latloc = 35
        return self
        
        
    def _plot_ce(self):
        """Get Canada East plotting info.
        
        Returns
        -------
        self
            Adds attributes used for plotting
        """
        self.loc_names = ['Ontario',b'Qu\xe9bec','Newfoundland and Labrador',
                          'New Brunswick','Prince Edward Island','Nova Scotia']
        # Get geometries
        self._get_geoms('admin_1_states_provinces_shp', 'name')
        
        # Workout string color
        self._get_str_col()
        
        # Latitude and longitude location of text
        self.lonloc = -90
        self.latloc = 47
        return self
        
        
    def _plot_wc(self):
        """Get West Coast plotting info.
        
        Returns
        -------
        self
            Adds attributes used for plotting
        """
        # Add region infront of self.rank
        self.rank = 'WC: '+self.rank
        
        self.loc_names = ['California','Oregon','Washington','Hawaii',
                          'Wyoming','Idaho','Alaska','Montana']
        # Get geometries
        self._get_geoms('admin_1_states_provinces_shp', 'name')
        
        self.strcol = 'black'
        
        # Latitude and longitude location of text
        self.lonloc = -155
        self.latloc = 40
        return self
        
        
    def _plot_a(self):
        """Get Asia plotting info.
        
        Returns
        -------
        self
            Adds attributes used for plotting
        """
        self.loc_names = ['Kazakhstan','Uzbekistan','Turkmenistan',
                          'Afghanistan','Pakistan','Tajikistan','Kyrgyzstan',
                          'China','India','Nepal','Mongolia','Bangladesh',
                          'Bhutan','Sri Lanka','Myanmar','Thailand','Lao PDR',
                          'Vietnam','Cambodia','Dem. Rep. Korea',
                          'Republic of Korea','Japan','Taiwan','Philippines',
                          'Malaysia','Brunei','Indonesia','Azerbaijan']
        self._get_geoms('admin_0_countries', 'NAME_LONG')
        self.loc_names = ['Tomsk','Chukchi Autonomous Okrug','Chelyabinsk',
                          'Kurgan','Yamal-Nenets','Sverdlovsk','Khanty-Mansiy',
                          'Omsk',"Tyumen'",'Altay','Gorno-Altay','Kemerovo',
                          'Khakass','Novosibirsk','Evenk','Irkutsk',
                          'Krasnoyarsk','Taymyr','Tuva','Buryat',
                          'Ust-Orda Buryat','Aga Buryat','Amur','Chita',
                          "Primor'ye",'Chukot','Yevrey','Khabarovsk',
                          'Maga Buryatdan','Sakhalin','Kamchatka']
        self._get_geoms('admin_1_states_provinces_shp', 'name')       

        # Workout string color
        self._get_str_col()
        
        # Latitude and longitude location of text
        self.lonloc = 85
        self.latloc = 35
        return self

        
    def _plot_aa(self):
        """Get Australasia plotting info.
        
        Returns
        -------
        self
            Adds attributes used for plotting
        """
        self.loc_names = ['Australia','New Zealand','Papua New Guinea',
                          'Antarctica']
        # Get geometries
        self._get_geoms('admin_0_countries', 'NAME_LONG')        

        # Workout string color
        self._get_str_col()
        
        # Latitude and longitude location of text
        self.lonloc = 120
        self.latloc = -25
        return self
        
        
    def _plot_en(self):
        """Get Europe North plotting info.
        
        Returns
        -------
        self
            Adds attributes used for plotting
        """
        self.loc_names = ['Aland Islands','Bulgaria','Belarus','Bouvet Island',
                          'Czech Republic','Denmark','Estonia','Finland',
                          'Faroe Islands','Greenland','Hungary','Iceland',
                          'Lithuania','Latvia','Norway','Poland','Romania',
                          'Svalbard','Jan Mayen','Slovakia','Sweden','Ukraine',
                          'Kaliningrad','Komi','Leningrad',
                          'City of St. Petersburg','Adygey',
                          'Karachay-Cherkess','Ingush','Kabardin-Balkar',
                          'North Ossetia',"Stavropol'",'Murmansk','Novgorod',
                          'Pskov','Bryansk','Smolensk','Karelia',
                          "Arkhangel'sk",'Ivanovo','Kostroma','Nizhegorod',
                          "Tver'",'Vologda',"Yaroslavl'",'Kaluga','Kursk',
                          'Lipetsk','Moskovsskaya','Moskva','Orel','Rostov',
                          'Tula','Volgograd','Belgorod','Krasnodar','Mordovia',
                          'Penza',"Ryazan'",'Tambov','Vladimir','Voronezh',
                          'Bashkortostan','Nenets','Kirov','Mariy-El','Udmurt',
                          "Astrakhan'",'Chuvash','Kalmyk','Orenburg','Samara',
                          'Saratov','Tatarstan',"Ul'yanovsk",'Chechnya',
                          'Dagestan','Murmansk','Komi-Permyak',"Perm'"]
        self._get_geoms('admin_0_countries', 'NAME_LONG')
        self.loc_names = ['Kaliningrad']        
        self._get_geoms('admin_0_map_subunits', 'NAME_LONG')
        self.loc_names = ['Komi','Leningrad','City of St. Petersburg','Adygey',
                          'Karachay-Cherkess','Ingush','Kabardin-Balkar',
                          'North Ossetia',"Stavropol'",'Murmansk','Novgorod',
                          'Pskov','Bryansk','Smolensk','Karelia',
                          "Arkhangel'sk",'Ivanovo','Kostroma','Nizhegorod',
                          "Tver'",'Vologda',"Yaroslavl'",'Kaluga','Kursk',
                          'Lipetsk','Moskovsskaya','Moskva','Orel','Rostov',
                          'Tula','Volgograd','Belgorod','Krasnodar','Mordovia',
                          'Penza',"Ryazan'",'Tambov','Vladimir','Voronezh',
                          'Bashkortostan','Nenets','Kirov','Mariy-El','Udmurt',
                          "Astrakhan'",'Chuvash','Kalmyk','Orenburg','Samara',
                          'Saratov','Tatarstan',"Ul'yanovsk",'Chechnya',
                          'Dagestan','Murmansk','Komi-Permyak',"Perm'"]        
        self._get_geoms('admin_1_states_provinces_shp', 'name')

        self._get_str_col()
        
        # Latitude and longitude location of text
        self.lonloc = 20
        self.latloc = 50
        return self 


    def _plot_es(self):
        """Get Europe South plotting info.
        
        Returns
        -------
        self
            Adds attributes used for plotting
        """
        self.loc_names = ['Andorra','Switzerland','Cyprus','Spain','France',
                          'Guernsey','Gibraltar','Italy','Jersey','Monaco',
                          'Malta','Montenegro','Portugal','San Marino',
                          'Turkey','Vatican','Georgia','Armenia']
        # Get geometries
        self._get_geoms('admin_0_countries', 'NAME_LONG')        

        self.strcol = 'black'
        
        # Latitude and longitude location of text
        self.lonloc = -30
        self.latloc = 40
        return self
        
        
    def _plot_ec(self):
        """Get Europe Central plotting info.
        
        Returns
        -------
        self
            Adds attributes used for plotting
        """
        self.loc_names = ['Albania','Austria','Belgium',
                          'Bosnia and Herzegovina',
                          'Federation of Bosnia and Herzegovina',
                          'Republic Srpska','Germany','United Kingdom',
                          'Greece','Croatia','Isle of Man','Ireland',
                          'Liechtenstein', 'Luxembourg','Moldova','Macedonia',
                          'Netherlands','Serbia','Slovenia','Kosovo']
        # Get geometries
        self._get_geoms('admin_0_countries', 'NAME_LONG')        

        self.strcol = 'black'
        
        # Latitude and longitude location of text
        self.lonloc = -30
        self.latloc = 52
        return self


    def _plot_ame(self):
        """Get Africa Middle East plotting info.
        
        Returns
        -------
        self
            Adds attributes used for plotting
        """
        self.loc_names = ['South Africa','Lesotho','Swaziland','Mozambique',
                          'Zimbabwe','Botswana','Namibia','Zimbabwe',
                          'Madagascar','Zambia','Angola','Malawi','Tanzania',
                          'Burundi','Rwanda',
                          'Democratic Republic of the Congo',
                          'Republic of the Congo','Gabon','Equatorial Guinea',
                          'Uganda','Kenya','Somalia','Somaliland','Ethiopia',
                          'South Sudan','Central African Republic','Cameroon',
                          'Nigeria','Benin','Togo','Ghana',"Côte d'Ivoire",
                          'Liberia','Sierra Leone','Guinea','Guinea-Bissau',
                          'Senegal','The Gambia','Mali','Burkina Faso','Niger',
                          'Chad','Sudan','Djibouti','Eritrea','Egypt','Libya',
                          'Algeria','Mauritania','Western Sahara','Morocco',
                          'Tunisia','Israel','Palastine','Gaza Strip',
                          'West Bank','Jordan','Saudi Arabia','Yemen','Oman',
                          'United Arab Emirates','Qatar','Bahrain','Iraq',
                          'Syria','Lebanon','Kuwait','Iran']
        # Get geometries
        self._get_geoms('admin_0_countries', 'NAME_LONG') 

        # Workout string color
        self._get_str_col()
        
        # Latitude and longitude location of text
        self.lonloc = 10
        self.latloc = 10
        return self 
        
        
    def _plot_ca(self):
        """Get Central America plotting info.
        
        Returns
        -------
        self
            Adds attributes used for plotting
        """
        self.loc_names = ['Mexico','Guatemala','Belize','El Salvador',
                          'Honduras','Nicaragua','Costa Rica','Panama','Cuba',
                          'The Bahamas','Jamaica','Turks and Caicos Islands',
                          'Haiti','Dominican Republic','Puerto Rico',
                          'Virgin Islands','Anguilla','St Kitts and Nevis',
                          'Montserrat','Guadeloupe','Dominica','Martinique',
                          'St Lucia','St Vincent and the Grenadines',
                          'Barbados','Grenada','Trinidad and Tobago']
        # Get geometries
        self._get_geoms('admin_0_countries', 'NAME_LONG')

        # Workout string color
        self._get_str_col()
        
        # Latitude and longitude location of text
        self.lonloc = -115
        self.latloc = 10
        return self 
        

    def _plot_sa(self):
        """Get South America plotting info.
        
        Returns
        -------
        self
            Adds attributes used for plotting
        """
        self.loc_names = ['Colombia','Venezuela','Guyana','Suriname','Ecuador',
                          'Peru','Brazil','Bolivia','Paraguay','Uruguay',
                          'Argentina','Chile','French Guiana']
        # Get geometries
        self._get_geoms('admin_0_countries', 'NAME_LONG')
        self.loc_names = ['French Guiana']        
        self._get_geoms('admin_0_map_units', 'NAME_LONG')        

        # Workout string color
        self._get_str_col()
        
        # Latitude and longitude location of text
        self.lonloc = -70
        self.latloc = -10
        return self 
        
        
    def _get_geoms(self, _f, attname):
        """Get Shapely geometries of locations from Natural Earth.
        
        Parameters
        ----------
        _f : str
            Natural Earth file name
        attname : str
            Expected attribute name
            
        Returns
        -------
        self.geoms : list of geometries
        """
        filename = shapereader.natural_earth(resolution='10m',
                                             category='cultural',
                                             name=_f)
        reader = shapereader.Reader(filename)
        records = list(reader.records())
        for _loc in records:
            if _loc.attributes[attname] in self.loc_names:
                if _loc.attributes[attname] == 'France':
                    # Only want mainland France. Not its territories
                    try:
                        self.geoms += _loc.geometry[-1]
                    except TypeError:
                        self.geoms.append(_loc.geometry[-1])
                else:
                    try:
                        self.geoms += _loc.geometry
                    except TypeError:
                        self.geoms.append(_loc.geometry)                    
        return self

    
    def _get_str_col(self):
        """Take into account the color or the polygon to work out the color of
        the string.
        
        Returns
        -------
        array : RGBA colors from the given colormap
        """
        cnum = len(self.ds_sorted.coords['regions']) - self.regcount - 1
        # Use black for middle colors
        if cnum > 7 and cnum < 11:
            self.strcol = 'black'
        else:
            self.strcol = self.colors[cnum]
        return self
    
    
    def cityplot(self, city=None, state=None, column=None, how=None):
        """Create a plot showing a map of the city with data for each gym.
        
        Parameters
        ----------
        city : string
            Name of the city.
            Check if the city is in https://github.com/raybellwaves/cfanalytic\
            s/blob/master/Data/Affiliate_list.csv
        state : string
            If US, two letter string e.g. SC is South Carolina
        column : string
            Name of column in the file.
            Must be X_rank.
        how : string
            Name of method to analyze the data.
            P0 : 5th percentile.
            
        Returns
        -------
        matplotlib.pyplot.figure : matplotlib.pyplot.figure
            Creates Crossfit city plot.
            
        Example
        -------
        cfa.Cfplot('Men_Rx_2018').cityplot(city='Miami', column='Overall_rank',
        ...                                how='P0')
        """
        if city is None:
            raise ValueError('Must enter city.')           
        self.city = city

        self.state = state
        # If column and how are not provided use 'Overall_rank' and 'P0'
        if column is None:
            self.column = 'Overall_rank'
        else:
            self.column = column
        if how is None:
            self.how = 'P0'
        else:
            self.how = how
        
        # Make sure a X_rank column was entered
        if self.column.split('_')[-1] != 'rank':
            raise ValueError('Column should be a rank column.')
            
        # Get cities where gyms are located
        self._get_city_gyms()        
        
        # Create xr.DataArray to store the ranks
        da = xr.DataArray(np.full((len(self.df_gyms), 2000),
                                  np.nan, dtype=np.double),
            coords=[self.df_gyms['Affiliate_name'].values,
                    np.arange(2000)],
            dims=['gyms','athletes'])
        # Fill with data for each gym
        for i, gym_id in enumerate(self.df_gyms['Affiliate_name'].values):
            row = self.df_gyms[
                    self.df_gyms['Affiliate_name'] == gym_id]
            aid = row['Affiliate_id'].values
            df = self.df.query('Affiliate_id =='+str(aid))
            da.loc[gym_id, 0:len(df)-1] = df[self.column].values
        # Drop gyms where no one entered the open
        da = da.dropna('gyms', how='all')
        # Update self.df_gyms with only these gyms
        self.df_gyms = self.df_gyms.loc[
                self.df_gyms['Affiliate_name'].isin(da.coords['gyms'].values)]       

        # Some gyms don't have latitude and longitude. Drop these
        i = np.where(self.df_gyms['Latitude'].values == '')
        da.loc[self.df_gyms['Affiliate_name'].values[i], :] = np.nan
        da = da.dropna('gyms', how='all')
        # Update self.df_gyms with only these gyms
        self.df_gyms = self.df_gyms.loc[
                self.df_gyms['Affiliate_name'].isin(da.coords['gyms'].values)]

        # Create a data array for athelete names
        mol_ext = list()
        _da = da.copy(deep=True).astype(str)
        for i, gym_id in enumerate(self.df_gyms['Affiliate_name'].values):
            row = self.df_gyms[
                    self.df_gyms['Affiliate_name'] == gym_id]
            aid = row['Affiliate_id'].values[0]
            mol_ext.append(str(aid))
            df = self.df.query('Affiliate_id =='+str(aid))
            _da.loc[gym_id, 0:len(df)-1] = df['Name'].values
        # Print url for Matt Kruse's awesome site
        mol_ur = 'http://myopenleaderboard.com/?'+",".join(mol_ext)
        print('')
        print('Printing url to check the results on myopenleaderboard.com...')        
        print(mol_ur)
        print('')

        # Create a data array for nthletes        
        _da2 = da[:,0].copy(deep=True).drop('athletes')       
        _da2.values = np.count_nonzero(~np.isnan(da.values), axis=1)
        
        # Create a data array for address        
        _da3 = _da[:,0].copy(deep=True)
        # Create a data array for website
        _da4 = _da3.copy(deep=True)
        # Create a data array for phone
        _da5 = _da3.copy(deep=True)        
        # Create a data array for lat
        _da6 = da[:,0].copy(deep=True).drop('athletes')
        # Create a data array for lon
        _da7 = _da6.copy(deep=True)
        for index, row in self.df_gyms.iterrows():
            _da3.loc[row['Affiliate_name']] = row['Address']
            _da4.loc[row['Affiliate_name']] = row['Website']
            _da5.loc[row['Affiliate_name']] = row['Phone']           
            _da6.loc[row['Affiliate_name']] = row['Latitude']
            _da7.loc[row['Affiliate_name']] = row['Longitude']
            
        # Print out extent of city map
        #print(_da7.min(), _da7.max(), _da6.min(), _da6.max())
        #sys.exit()

        # Create xr.Dataset of all the data
        #ds = xr.Dataset({self.column:da, 'athlete_names':_da, 'nathletes':_da2,
        #                 'address':_da3, 'website':_da4, 'phone':_da5,
        #                 'latitude':_da6, 'longitude':_da7})
        # Create xr.Dataset of data to plot
        ds = xr.Dataset({self.how:da[:,0].drop('athletes'), 
                          'athlete_names':_da[:,0].drop('athletes'),
                          'address':_da3, 'website':_da4, 'phone':_da5,
                          'latitude':_da6, 'longitude':_da7})

        # Data analysis method        
        if self.how[0] == 'P':
            # Percentile method
            percentile_val = float(self.how.split('P')[-1])/100.
            if percentile_val != 0.0:
                raise ValueError('Only how=P0 implemented.')            
            if percentile_val > 0.0:
                # Drop 'athlete_names' data array
                ds = ds.drop('athlete_names')
            ds[self.how].values = \
            da.quantile(percentile_val, dim='athletes').astype(int)

        # Print the data
        self._show_city_data(ds)
        
        # Plot the data
        self._plot_city(self.ds_sorted)        

           
    def _get_city_gyms(self):
        """Return a Dataframe of the gyms in the specificed city.
        This is obtained from https://github.com/raybellwaves/cfanalytics/blob\
        /master/Data/Affiliate_list.csv
            
        Returns
        -------
        self.df_gyms : pd.Dataframe
            Gyms in the city and other info.
        """
        if not os.path.isfile(self._dir+'Affiliate_list'):
            raise OSError('Affiliate_list must be in the same directory as the\
                          open data: '+self._dir)
        df_affiliate = pd.read_pickle(self._dir+'Affiliate_list')
        
        # What is the maximum number of gyms in a city
        #_df = df_affiliate['City']
        #unique, counts = np.unique(_df.values,
        #                           return_counts=True)
        #print(unique[np.argmax(counts)])
        
        # Obtain city column
        cities = df_affiliate.loc[:,'City'].values
        
        # Check if self.city is in cities
        if not self.city in cities:
            raise ValueError('city: '+self.city+' is not in Affiliate_list')
        
        # Get gyms in the city
        df_gyms = df_affiliate.loc[df_affiliate['City'] == self.city]

        # Old method... remove eventually...
        # The city could be located in multiple countries
        # Keep those that are most frequeny in a country
        # If this does not work for other cities 
        # revist it and maybe add country as an input
        # Check how many countries there are:
        #unique, counts = np.unique(df_gyms.loc[:,'Country'].values,
        #                           return_counts=True)
        #if len(unique) > 1:
        #    ix = np.argmax(counts)
        #    df_gyms = df_gyms.loc[df_affiliate['Country'] == unique[ix]]
            
        if self.state is not None:
            df_gyms = df_gyms.loc[df_gyms['State'] == self.state]

        self.df_gyms = df_gyms
        return self


    def _show_city_data(self, ds):
        """Print the data.
        
        Parameters
        ----------
        ds : xr.Dataset
            xr.Dataset with city analysis results.
            Coordinates: gyms.
            
        Returns
        -------
        sorted : xr.Dataset
            Sorted dataset.
        """
        ds_sorted = ds.sortby(ds[self.how])
        print('Printing results for...')
        print(self.fname)
        print(self.city)
        print(self.column)
        if self.how == 'P0':
            print('rank, name, gym, '+self.how)
        for i in range(0, len(ds_sorted.coords['gyms'])):
            print(i+1,',',ds_sorted['athlete_names'].values[i],',',
                  ds_sorted.coords['gyms'].values[i],',',
                  ds_sorted[self.how].values[i])
        self.ds_sorted = ds_sorted
        print('')
        print('Printing results in reddit table format...')
        print('Rank | Name | Gym | '+self.column+' '+self.how)
        print('---- | ---- | --- | ---------------')
        for i in range(0, len(ds_sorted.coords['gyms'])):
            print(str(i+1)+' | '+ds_sorted['athlete_names'].values[i]+' | '+\
                  ds_sorted.coords['gyms'].values[i]+' | '+\
                  str(ds_sorted[self.how].values[i]))      
        return self


    def _plot_city(self, ds):
        """Plot the results of gyms in a city.
        
        Parameters
        ----------
        self.ds_sorted : xr.Dataset
            xr.Dataset with Coordinates: gyms.
            
        Returns
        -------
        matplotlib.pyplot.figure : matplotlib.pyplot.figure
            Creates city plot.        
        """
        # Create extend of map [W, E, S, N]
        extent = [ds['longitude'].values.min(), ds['longitude'].values.max(),
                  ds['latitude'].values.min(), ds['latitude'].values.max()]

        # Setup colors
        colors = cm.nipy_spectral(np.linspace(0,1,len(ds['gyms'])))
        
        # Get google map. Scale is for more details. Mapytype can have
        # terrain' or 'satellite'
        g = GoogleVisibleMap(x=[extent[0], extent[1]], y=[extent[2],
                                extent[3]], scale=4, maptype='terrain')
        ggl_img = g.get_vardata()
        
        # Plot map
        fig, ax = plt.subplots(1, 1, figsize=(20,20))
        sm = Map(g.grid, factor=1, countries=False)
        sm.set_rgb(ggl_img)
        sm.visualize(ax=ax)
        # Plot gym points
        for i in range(0, len(ds['gyms'])):
            # Create label
            self.regcount = i
            self._rank() # Add self.rank
            _label = self.rank+' '+ds['gyms'].values[i]+': '+\
            ds['athlete_names'].values[i]+' ('+str(ds[self.how].values[i])+')'
            x, y = sm.grid.transform(ds['longitude'].values[i],
                                     ds['latitude'].values[i])
            ax.scatter(x, y, color=colors[i], s=400, label=_label)
        plt.title(self.fname+' | '+self.city+' | '+self.column+' | '+self.how)

        # Shrink current axis by 20% to make room for legend
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        
        plt.savefig(self.plotdir+self.fname+'_'+self.city+'_'+self.column+'_'+\
                    self.how+'.png', bbox_inches = 'tight')
        #plt.savefig(self.plotdir+self.fname+'_'+self.city+'_'+self.column+\
        #            self.how+'.png', bbox_inches = 'tight', format='eps')
        plt.show()