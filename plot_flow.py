# -*- coding: utf-8 -*-
"""
This script read a SWAT output.rch file and plot against USGS observed flow.

Created on Fri Feb 14 00:21:31 2020

@author: Michael Ou

usage:
    python swat_plot.py 
"""




import os
import pandas as pd
import matplotlib.pyplot as plt
from urllib.request import urlopen

from swat_reader import swat_reader
from usgs_water_data_reader import usgs_data_reader
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot streamflow from SWAT output.rch (against USGS measurements')
    parser.add_argument('TxtInOut', help='TxtInOut directory path, required.')
    parser.add_argument('-b', '--subbasin',  default=[1], type=int,  nargs='*', help='Desired subbasin index/indices to save (default: %(default)s).')
    parser.add_argument('-o', '--output',    default='.', metavar='output_dir', help='Output directory for plots (default: %(default)s).')
    parser.add_argument('-p1', action='store_true', help='All the reaches will be plot on the same charts for each variable. ')
    parser.add_argument('-u', '--unit',  default='m', choices=['m','f','af'], help='The unit for flow volume m:meters; f:feet; af:acre-feet')
    parser.add_argument('-t', '--timeunit',  default='s', choices=['s','d'], help='The unit for flow volume s:second; d:day; m:month; y:year')
    parser.add_argument('-p', '--prefix',  default='', help='Prefix for plot file names')
    parser.add_argument('--usgs', nargs='*', help='The USGS site numbers to ')
    parser.add_argument('-n', type=int,   default=100, metavar='minimum_number_record', help='The minimum observation record number of a gauge. \
                        If the number of record during the output period is smaller than this number, the usgs site will not included in the plot. (default: %(default)s).')

    
    
    # parser.print_help()
    args = parser.parse_args('D:\\WorkSync\\CPNRD-UnSWAT\\ArcSWAT_2021\\Scenarios\\Default-Irrigation\\TxtInOut -b 8 14 15 22 53 72 84 91 92 93 99 118 119 123\
            --usgs 06774000 06794650 06772898 06773500 06772775 06772100 06772000 06771500 06769000 06769525 06770500 06770000 06770200 06767500 -p flow -n 100'.split())
    
    args = parser.parse_args()
    
    # print(args)
    if args.usgs is not None:
        assert len(args.subbasin) == len(args.usgs), 'The stat method numbers need to match the variale number.'
            
    # read the output.rch file:
    swatreader = swat_reader(args.TxtInOut)
    df_out = swatreader.read_rch()
    
    # filter the subbasins
    df_filter = swat_reader.filter(df_out, args.subbasin, ["FLOW_OUTcms"])
    
    # convert units if necessary
    time_factor = dict(s=1., d=86400.)
    time_label = dict(s='sec', d='day')
    length_factor = dict(m=1., f=35.3147, af=0.000810714)
    length_factor_usgs = dict(m=0.0283168, f=1, af=1/43560)
    length_label = dict(m='meter$^3$', f='feet$^3$', af='acre-feet')


    df_filter *= length_factor[args.unit] * time_factor[args.timeunit]
    df_filter.columns = [f'Simulated']
    
    # download the USGS data
    start_date = df_filter.index.levels[1].min()
    end_date   = df_filter.index.levels[1].max()
    for s, u in zip(args.subbasin, args.usgs):
        
        # read flow
        url  = usgs_data_reader.create_daily_streamflow_url([u], begin_date=f'{start_date:%Y-%m-%d}', end_date=f'{end_date:%Y-%m-%d}')
        flow = usgs_data_reader.read_usgs_rdb(url) 

        # read name of the gauge
        for l in urlopen(url): 
            if u.encode() in l: 
                break
        
        
        fig, ax = plt.subplots(figsize=(8, 5))
        
        df_filter.loc[s].plot(ax=ax, label='Simulated', legend=True)
        if flow.shape[0] > args.n:
            observed = flow.drop(['agency_cd', 'site_no'], axis=1).set_index('datetime').iloc[:,0]
            observed = pd.to_numeric(observed, errors='coerce').dropna() * length_factor_usgs[args.unit]
            observed.index = pd.DatetimeIndex(observed.index)            
            observed.plot( ax=ax, label='Observed',  legend=True, linewidth=1)
            
        ax.set_title(l[1:].strip().decode())
        ax.set_xlabel('Time')
        ax.set_ylabel(f'Streamflow ({length_label[args.unit]}/{time_label[args.timeunit]})')
        fig.savefig(os.path.join(args.output, f'{args.prefix}{s}.png'), dpi=300)


