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
from usgs_water_data_reader import read_usgs_flow
import argparse

plt.style.use('ggplot')
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot streamflow from SWAT output.rch (against USGS measurements')
    parser.add_argument('TxtInOut', help='TxtInOut directory path, required.')
    parser.add_argument('-b', '--subbasin',  default=[1], type=int,  nargs='*', help='Desired subbasin index/indices to save (default: %(default)s).')
    parser.add_argument('-u', '--usgs', nargs='*', help='The USGS site numbers corresponding to the subbasins')
    parser.add_argument('-o', '--output',    default='.', metavar='output_dir', help='Output directory for plots (default: %(default)s).')
    parser.add_argument('-p1', action='store_true', help='All the reaches will be plot on the same charts for each variable. ')
    parser.add_argument('-l', '--lengthunit',  default='m', choices=['m','f','af'], help='The unit for flow volume m:meters; f:feet; af:acre-feet')
    parser.add_argument('-t', '--timeunit',  default='s', choices=['s','d'], help='The unit for flow volume s:second; d:day; m:month; y:year')
    parser.add_argument('-p', '--prefix',  default='', help='Prefix for plot file names')
    parser.add_argument('--log', action='store_true',  default=False, help='Prefix for plot file names')
    parser.add_argument('-slw', type=float,  default=1.0, help='Line width for simulated streamflow')
    parser.add_argument('-olw', type=float,  default=0.8, help='Line width for observed streamflow')
    parser.add_argument('-sls', type=str,  default='-', help='Line style for simulated streamflow')
    parser.add_argument('-ols', type=str,  default='-', help='Line style for observed streamflow')
    parser.add_argument('-fs', '--figsize', default=(8, 4), nargs=2, help='Figure size')
    parser.add_argument('-n', type=int,   default=100, metavar='minimum_number_record', help='The minimum observation record number of a gauge. \
                        If the number of record during the output period is smaller than this number, the usgs site will not included in the plot. (default: %(default)s).')

    
    
    # parser.print_help()
    # args = parser.parse_args('D:\\WorkSync\\CPNRD-UnSWAT\\ArcSWAT_2021\\Scenarios\\Default-Irrigation\\TxtInOut -b 8 14 15 22 53 72 84 91 92 93 99 118 119 123\
    #         --usgs 06774000 06794650 06772898 06773500 06772775 06772100 06772000 06771500 06769000 06769525 06770500 06770000 06770200 06767500 -p flow -n 100'.split())
    
    args = parser.parse_args()
    
    # print(args)
    if args.usgs is not None:
        assert len(args.subbasin) == len(args.usgs), 'The subbasin number need to the gaging station number.'
            
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


    df_filter *= length_factor[args.lengthunit] * time_factor[args.timeunit]
    df_filter.columns = ['Simulated']
    # print('df_fileter:\n', df_filter)
    # download the USGS data
    start_date = df_filter.index.levels[1].min()
    end_date   = df_filter.index.levels[1].max()
    print('The starting date of the output file is:', start_date)
    print('The ending date of the output file is  :', end_date)
    
    output_dir = args.output
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    
    for s, u in zip(args.subbasin, args.usgs):
        
        # read flow
        
        # read flow
        flow, gauge_names  = read_usgs_flow([u], '{:%Y-%m-%d}'.format(start_date), '{:%Y-%m-%d}'.format(end_date), 'D')
        flow = flow.iloc[:, 1]
        flow.index = pd.DatetimeIndex(flow.index)
        if swatreader.cio['IPRINT'] == '0': # monthly output
            flow = pd.to_numeric(flow).resample('M').mean()
        elif swatreader.cio['IPRINT'] == '1':
            pass
        else:
            raise NotImplementedError('IPRINT is {} for annual output.\nPlotting annual output is not supported.'.format(args.iprint))
        

        
        fig, ax = plt.subplots(figsize=args.figsize)
        df_filter.loc[s].plot(ax=ax, label='Simulated', legend=True, linewidth=args.slw, linestyle=args.sls)
        csv = df_filter.loc[s]
        csv.columns = ['Simulated']
        
        if flow.shape[0] > args.n:
            
            observed = flow
                
            observed = pd.to_numeric(observed, errors='coerce').dropna() * length_factor_usgs[args.unit]
            observed.index = pd.DatetimeIndex(observed.index)            
            observed.plot( ax=ax, label='Observed',  legend=True, linewidth=args.olw, linestyle=args.ols)
            observed.name = 'Observed'
            csv = pd.concat([csv, observed], axis=1)
        
        if args.log:
            ax.set_yscale('log')
        ax.set_title(gauge_names[u])
        ax.set_xlabel('Time')
        ax.set_ylabel('Streamflow ({}/{})'.format(length_label[args.unit], time_label[args.timeunit]))
        fig.savefig(os.path.join(args.output, '{}{}.png'.format(args.prefix, s)), dpi=300)
        csv.to_csv(os.path.join(args.output, '{}{}.csv'.format(args.prefix, s)))

    print('Plots are generated successfully at {}'.format(os.path.abspath(args.output)))

