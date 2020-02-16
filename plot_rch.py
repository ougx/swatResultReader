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

from swat_reader import swat_reader
from usgs_water_data_reader import usgs_data_reader
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot simulated results in SWAT output.rch')
    parser.add_argument('TxtInOut', help='TxtInOut directory path, required.')
    parser.add_argument('-b', '--subbasin',  default=[1], type=int,  nargs='*', help='Desired subbasin index/indices to save (default: %(default)s).')
    parser.add_argument('-v', '--variable',  default=["FLOW_OUTcms"], nargs='*', help='Desired variable to save (default: %(default)s).')
    parser.add_argument('-o', '--output',    default='.', metavar='output_dir', help='Output directory for plots (default: %(default)s).')
    parser.add_argument('-s', '--stat', metavar='stat_method', nargs='*', choices='sum mean std sem max min median first last'.split(), 
                        help='''
                        Calculate and save the statistics using Pandas resampling function to upscale the temporal frequency. 
                        Use -r or --resample to specify the resample frequency.
                        You can use one stat_method for all variables otherwise the number of stat_methods should equal to the number of variable to be saved.
                        Aggregating options: sum, mean, std, sem, max, min, median, first, last.                        
                        Reference: https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#resampling
                        ''')
    parser.add_argument('-f', '--freq', help='aggreation/resample frequency.')
    parser.add_argument('-p1', action='store_true', help='All the reaches will be plot on the same charts for each variable. ')
    parser.add_argument('-u', '--unit',  default='m', choices=['m','f','af'], help='The unit for flow volume m:meters; f:feet; af:acre-feet')
    parser.add_argument('-t', '--timeunit',  default='s', choices=['s','d','m', 'y'], help='The unit for flow volume s:second; d:day; m:month; y:year')
    parser.add_argument('-p', '--prefix',  default='', help='Prefix for plot file names')
    
    
    # parser.print_help()
    # args = parser.parse_args('D:\\WorkSync\\CPNRD-UnSWAT\\ArcSWAT_2021\\Scenarios\\Default-Irrigation\\TxtInOut -b 1 2 -v FLOW_OUTcms FLOW_INcms -f M -s mean sum'.split())
    
    args = parser.parse_args()
    # print(args)
    
    # make sure the correct resampling arguments are used
    assert (args.stat is None) == (args.freq is None), 'The freq and stat arguments need to both be specified to calculate statistics.'
    if args.stat is not None:
        if len(args.stat) == 1:
            args.stat = args.stat * len(args.variable)
        else:
            assert len(args.variable) == len(args.stat), 'The stat method numbers need to match the variale number.'
         
    # read the output.rch file:
    swatreader = swat_reader(args.TxtInOut)
    df_out = swatreader.read_rch()
    
    # filter and aggregate if specified
    df_filter = swat_reader.filter(df_out, args.subbasin, args.variable, args.freq, args.stat)
    
    # convert units if necessary
    time_factor = dict(s=1., d=86400., m=86400*30.4375, y=86400*365.25)
    time_label = dict(s='sec', d='day', m='month', y='year')
    length_factor = dict(m=1., f=35.3147, af=0.000810714)
    length_label = dict(m='meter$^3$', f='feet$^3$', af='acre-feet')
    
    
    for v in args.variable:
        # check if need to do unit conversion
        if v in ['FLOW_INcms', 'FLOW_OUTcms']:
            # cubic feet
            df_filter[v] *= length_factor[args.unit] * time_factor[args.timeunit]
            
            # if they plot together
            if args.p1:
                fig, ax = plt.subplots(figsize=(8, 5))
                for h in args.subbasin:
                    df_filter[v][h].plot(ax=ax, legend=True, label=f'Subbasin {h}')
                ax.set_ylabel('Streamflow ({}/{})'.format(length_label[args.unit], time_label[args.timeunit]))
                fig.savefig(os.path.join(args.output, '{}{}.png'.format(args.prefix, v)), dpi=300, bbox_inches='tight')
                
            else:
                for h in args.subbasin:
                    fig, ax = plt.subplots(figsize=(8, 5))
                    df_filter[v][h].plot(ax=ax)
                    ax.set_title('Simulated discharge for Subbasin {}'.format(h))
                    ax.set_ylabel('Streamflow ({}/{})'.format(length_label[args.unit], time_label[args.timeunit]))
                    fig.savefig(os.path.join(args.output, '{}{}-{}.png'.format(args.prefix, v, h)), dpi=300, bbox_inches='tight')
        
        else:
            
            # if they plot together
            if args.p1:
                fig, ax = plt.subplots(figsize=(8, 5))
                for h in args.subbasin:
                    df_filter[v][h].plot(ax=ax, legend=True, label=f'Subbasin ' + str(h))
                ax.set_ylabel(v)
                fig.savefig(os.path.join(args.output, '{}{}.png'.format(args.prefix, v)), dpi=300, bbox_inches='tight')
                
            else:
                for h in args.subbasin:
                    fig, ax = plt.subplots(figsize=(8, 5))
                    df_filter[v][h].plot(ax=ax)
                    ax.set_title(v + ' for Subbasin ' + str(h))
                    ax.set_ylabel(v)
                    fig.savefig(os.path.join(args.output, '{}{}-{}.png'.format(args.prefix, v, h)), dpi=300, bbox_inches='tight')
        
            

    print('Plots are generated successfully at {}'.format(os.path.abspath(args.output)))