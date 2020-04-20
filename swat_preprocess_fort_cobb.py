# -*- coding: utf-8 -*-
"""


@author: Michael Ou

This script is first developed by Gengxin (Michael) Ou on 2/18/2015 in R
https://gist.github.com/ougx/cb33a1cf761dea01fa0d#file-swat_preprocess-r

It was converted to Python on Sat Feb 15 18:54:54 2020

usage:
    python script.py ars_data.zip hint_wspd.zip

Study area:
    West  -98.590528    East  -98.439062 
    North  35.469812    South  35.285992 

"""

import os
import zipfile
import pandas as pd
import sys
import numpy as np
import datetime
#%% some parameters
ars_stations = list(range(101, 115)) #+ [207, 215]
start_date = np.datetime64('2006-01-01')
end_date   = np.datetime64('2019-12-31')

#ars_weather_var = {'pcp':('RAINt', 1.0), 'rh':('RELHa', 0.01), 'tmp':(['TAIRx', 'TAIRn'], 1.0), 'srad':('SRADt', 1.0)}
ars_weather_var = {'pcp':('RAINt', 1.0)}

output_dir = 'FcWeatherData'


assert len(sys.argv) > 2, 'Specify the ARS data file and wind speed file\n{}'.format(sys.argv)
    



ars_zip = sys.argv[1]
wspd_zip = sys.argv[2]

assert os.path.exists(ars_zip),  'The ARS weather data file "{}" does not exist.'.format(ars_zip)
assert os.path.exists(wspd_zip), 'The wind speed data file "{}" does not exist.'.format(wspd_zip)

if not os.path.exists(output_dir):
    os.mkdir(output_dir)


#%% weather except for precipitation
# http://www.mesonet.org/index.php/site/about/daily_summaries

meso_sites = pd.read_csv('http://www.mesonet.org/index.php/api/siteinfo/from_all_active_with_geo_fields/format/csv/').set_index('stid')
meso_weather_var = pd.DataFrame({'offset':(0., 32., 0., 0., 0.), 
                                 'scale':(0.4470389, 5./9., 1., 0.01, 25.4), 
                                 'cols':(['WSPD'], ['TMAX', 'TMIN'], ['ATOT'], ['HAVG'], ['RAIN'])},
                                 index=['wspd', 'tmp', 'srad', 'rh', 'pcp'])
    
filename = os.path.basename(wspd_zip).strip().split('.')[0] 
with zipfile.ZipFile(wspd_zip, 'r') as datazip:
    with datazip.open('{}.csv'.format(filename)) as f:
        df_meso = pd.read_csv(f)
df_meso.index = df_meso.apply(lambda x: datetime.datetime(x['YEAR'], x['MONTH'], x['DAY']), axis=1)
df_meso = df_meso[start_date: end_date]
sites = df_meso['STID'].unique()

#print(df_meso.head())
#print(df_meso.columns)

for v, r in meso_weather_var.iterrows():
    
    # do unit conversion
    vv = df_meso.loc[:, r.cols]
    df_meso.loc[:, r.cols] = np.where(vv.abs() < 900, (vv - r.offset) * r.scale, np.nan) 
    if v == 'tmp':
        print(df_meso.loc[:, r.cols])
        
    if v == 'pcp':
        df_meso.loc[:, r.cols] = df_meso.loc[:, r.cols].fillna(0.)
    else:
        df_meso.loc[:, r.cols] = df_meso.loc[:, r.cols].fillna(method='pad')
    
    
    # write list
    with open(os.path.join(output_dir, 'list_{}.txt'.format(v)),'w') as flist:
        flist.write('ID,NAME,LAT,LONG,ELEVATION\n')
    
        stid = 100
        for g, df in df_meso.groupby('STID'):
            flist.write('{},{}{},{},{},{}\n'.format(stid, v, g, *meso_sites.loc[g, ['nlat', 'elon', 'elev']])); stid += 1
            
            csv = os.path.join(output_dir, '{}{}.txt'.format(v, g))
            with open(csv,'w') as fo:
                fo.write('{:%Y%m%d}\n'.format(pd.to_datetime(start_date)))
                df.loc[:, r.cols].to_csv(fo, header=False, index=False)

        
        



#%%
##################################### ARS Micronet #################################### 

#read and combine the ars data
# STID - station ID -- required
# DM - day of the month (CST) -- required
# RAINt - total rainfall (mm); See Notes
# SRADt - total solar radiation (MJ/m^2)
# RELH(a/x/n) - (ave/max/min) relative humidity at 1.5 m (%)
# TAIR(a/x/n) - (ave/max/min) air temperature at 1.5 m (deg C)
# TS05(a/x/n) - (ave/max/min) soil temperature at 05 cm depth (deg C)
# TS10(a/x/n) - (ave/max/min) soil temperature at 10 cm depth (deg C)
# TS15(a/x/n) - (ave/max/min) soil temperature at 15 cm depth (deg C)
# TS25(a/x/n) - (ave/max/min) soil temperature at 25 cm depth (deg C)
# TS30(a/x/n) - (ave/max/min) soil temperature at 30 cm depth (deg C)
# TS45(a/x/n) - (ave/max/min) soil temperature at 45 cm depth (deg C)
# VW05(a/x/n) - (ave/max/min) volumetric water content at 5 cm depth (water fraction by volume)
# VW25(a/x/n) - (ave/max/min) volumetric water content at 25 cm depth (water fraction by volume)
# VW45(a/x/n) - (ave/max/min) volumetric water content at 45 cm depth (water fraction by volume)
# SKIN(a/x/n) - (ave/max/min) skin temperature (deg C) [available at a select number of Little Washita sites only]

# g - good (passed QC tests - extremely low probability of error)
# S - suspect (QC tests indicate some suspicion - low probability of error)
# W - warning (several QC test failures - high probability of error)
# F - failure (known error)
# M - missing (data not received)
# I - ignore
# N - not installed
# U - unknown
rain_fc = df_meso.query('STID == "FTCB"').loc[:, meso_weather_var.loc['pcp', 'cols']]
rain_fc = rain_fc.where(rain_fc.abs() < 900).fillna(0.)

df_rain = pd.DataFrame(np.nan, columns=['RAINt'], index=pd.date_range(start_date, end_date, freq='D'))
with zipfile.ZipFile(ars_zip, 'r') as datazip:
    months = pd.date_range(start_date, end_date, freq='MS')
    for s in ars_stations:
        for m in months:
            with datazip.open('{:%Y%m}f{}.txt'.format(m, s)) as f:
                df = pd.read_csv(f, skiprows=4, header=0, sep=' ', skipinitialspace =True)
                df.index = pd.date_range(m, periods=m.days_in_month, freq='D')
                df_rain.loc[df.index,:] = df 
                
        
        # deal with the missing data replaced by the FTCB station
        #print(df_rain.head())
        df_rain[:] = np.where(df_rain.abs()>900, rain_fc, df_rain)
        #print(df_rain.head())
        for k, v in ars_weather_var.items():
            val = (df_rain[v[0]] * v[1]).fillna(-99.0)
            csv = os.path.join(output_dir, '{}{}.txt'.format(k, s))
            with open(csv,'w') as fo:
                fo.write('{:%Y%m%d}\n'.format(pd.to_datetime(start_date)))
                val.to_csv(fo, header=False, index=False)


# Precipitation Gage Location Table
# ID Integer Gage identification number (not used by interface)
# NAME String max 8 chars Corresponding table name string
# LAT Floating point Latitude in decimal degrees
# LONG Floating point Longitude in decimal degrees
# ELEVATION integer Elevation of rain gage (m)

# Temperature Gage Location Table (ASCII Only)
# ID Integer Gage identification number (not used by interface)
# NAME String max 8 chars Corresponding table name string
# LAT Floating point Latitude in decimal degrees
# LONG Floating point Longitude in decimal degrees
# ELEVATION integer Elevation of temperature gage (m)

# solar/wind/relative humidity gage
# ID Integer Gage identification number (not used by interface)
# NAME String max 8 chars Corresponding table name string
# LAT Floating point Latitude in decimal degrees
# LONG Floating point Longitude in decimal degrees
# ELEVATION integer Elevation of solar/wind/RH gage (m)
                
ars_list = pd.read_csv('http://ars.mesonet.org/sites/default/files/2017-12/geoars_0.csv', skiprows=41, header=None)
ars_list_columns = {'NAME':1, 'LAT':7, 'LONG':8, 'ELEVATION':9}
ars_list = ars_list[[s.startswith('F') for s in ars_list[ars_list_columns['NAME']]]]

    
ars_list.index = ars_list[ars_list_columns['NAME']].apply(lambda x: int(x[-3:]))
ars_list.index.name = 'ID'
colnames = ars_list.columns.tolist()
for i in ars_list_columns:
    colnames[ars_list_columns[i]] = i
ars_list.columns = colnames
for k in ars_weather_var:
    ars_list['NAME'] = ars_list['NAME'].apply(lambda x: k+x[-3:])
    ars_list.loc[ars_stations, ['NAME', 'LAT', 'LONG', 'ELEVATION']].to_csv(os.path.join(output_dir, 'list_{}.txt'.format(k)))


##################################### USGS Streamflow ####################################
#processing streamflow data



print('\n\nPreprocesssing completed sucesuffuly')