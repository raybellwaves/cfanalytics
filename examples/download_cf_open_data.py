"""
Download Crossfit open data and save as a pandas DataFrame.
"""

import os
os.chdir('/Volumes/SAMSUNG/WORK/CFanalytics_2017/GitHub_folder/cfanalytics')
ddir = os.getcwd()+'/Data'
if not os.path.isdir(ddir):
    os.makedirs(ddir)
    

import cfanalytics as cfa

import time
start_time = time.time()


# Choose parameters to get data:
year = 2017
division = 2 # See L... in cfopendata
scaled = 0
batchpages = 50 # Number of pages to get at once

# Download crossfit data and save it in the 'Data' directory
cfa.cfopendata(year, division, scaled, batchpages, ddir)

print("script took " + str((time.time() - start_time) / 60.0) + " minutes")