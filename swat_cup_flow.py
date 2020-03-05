# -*- coding: utf-8 -*-
"""
This script read a SWAT output.rch file and plot against USGS observed flow.

Created on Fri Feb 14 00:21:31 2020

@author: Michael Ou

usage:
    python swat_plot.py 
"""




import pandas as pd
import argparse
from swat_reader import swat_reader
from usgs_water_data_reader import read_usgs_flow
import numpy as np
import os
from collections import OrderedDict
#%%
def write_observed_rch(filename, flows):
    '''
    write the RCH calibration file for SWAT-CUP
    '''
    header = '{:<6}: number of observed variables\n\n'.format(len(flows))
    station_head = 'FLOW_OUT_{:<4}: this is the name of the variable and the subbasin number to be included in the objective function\n' +\
    '{:<6}: number of data points for this variable as it follows below. First column is a sequential number from beginning\n'+\
    '      : of the simulation, second column is variable name and date (format arbitrary), third column is variable value.\n\n'

    with open(filename, 'w') as f:
        f.write(header)
        
        for k, v in flows.items():
            f.write(station_head.format(k, len(v)))
            v.to_csv(f, sep='\t', index=True, header=False, mode='a', line_terminator='\n')
            f.write('\n\n')

#write_observed_rch(os.path.join(args.output, 'Observed_rch.txt'), ob)

#%%

def write_observed_txt(filename, flows):
    '''
    write the RCH calibration file for SWAT-CUP
    '''
    header = '{:<6}: number of observed variables\n'.format(len(flows)) +\
        '5     : Objective function type, 1=mult,2=sum,3=r2,4=chi2,5=NS,6=br2,7=ssqr,8=PBIAS,9=KGE,10=RSR,11=MNS\n' +\
        '0.5   : min value of objective function threshold for the behavioral solutions\n' +\
        '1     : if objective function is 11=MNS (modified NS),indicate the power, p.\n\n\n\n' 
        
    station_head = 'FLOW_OUT_{:<4}: this is the name of the variable and the subbasin number to be included in the objective function\n' +\
        '{:<6}: weight of the variable in the objective function\n'+\
        '{:<6}: Dynamic flow separation. Not considered if -1. If 1, then values should be added in the forth column below after observations\n'+\
        '{:<6}: constant flow separation, threshold value. (not considered if -1)\n'+\
        '{:<6}: if separation of signal is considered, this is weight of the smaller values in the objective function\n'+\
        '{:<6}: if separation of signal is considered, this is weight of the larger values in the objective function\n'+\
        '{:<6}: percentage of measurement error\n'+\
        '{:<6}: number of data points for this variable as it follows below. First column is a sequential number from beginning\n'+\
        '      :  of the simulation, second column is variable name and date (format arbitrary), third column is variable value.\n\n'

    with open(filename, 'w') as f:
        f.write(header)
        
        for k, v in flows.items():
            f.write(station_head.format(k, v.weight, -1, -1, 1, 1, 10, len(v)))
            v.to_csv(f, sep='\t', index=True, header=False, line_terminator='\n')
            f.write('\n\n')
            

            
def write_var_file_rch(filename, rchs):
    '''
    write var_file.rch
    '''
    with open(filename, 'w') as f:
       
        for i in rchs:
            f.write('FLOW_OUT_{}.txt\n'.format(i))
                        
def write_extract_rch(filename, rchs, swatreader, nsub, start_date, end_date, iprint):
    '''
    write extract_rch.rch
    
    output.rch     : swat output file name
    2              : number of variables to get
    7   18         : variable column number(s) in the swat output file (as many as the above number)

    10             : total number of reaches (subbasins) in the project

    3              : number of reaches (subbasins) to get for the first variable
    1  3  7        : reach (subbasin) numbers for the first variable

    1              : number of reaches (subbasins) to get for the second variable (if no second variable delete this and next lines)
    7              : reach (subbasin) numbers for the second variable (ordered)

    1990           : beginning year of simulation not including the warm up period
    2001           : end year of simulation

    2              : time step (1=daily, 2=monthly, 3=yearly)

    '''
    with open(filename, 'w') as f:
        f.write('{:<15}: swat output file name\n'.format('output.rch'))
        f.write('{:<15}: number of variables to get\n'.format(1))
        f.write('{:<15}: variable column number(s) in the swat output file (as many as the above number)\n'.format(9 if swatreader.cio['ICALEN'] == '1' else 7))
        f.write('\n')
        f.write('{:<15}: total number of reaches (subbasins) in the project\n'.format(nsub))
        f.write('\n')
        f.write('{:<15}: number of reaches (subbasins) to get for the first variable\n'.format(len(rchs)))
        f.write('{:<15}: reach (subbasin) numbers for the first variable\n'.format(' '.join(map(lambda x: str(x), rchs))))
        f.write('\n')
        f.write('{:%Y           }: beginning year of simulation not including the warm up period\n'.format(start_date))
        f.write('{:%Y           }: end year of simulation\n'.format(end_date))
        f.write('\n')
        f.write('')
        f.write('{:<15}: time step (1=daily, 2=monthly, 3=yearly)\n'.format(1 if int(iprint) == 1 else 2))

def write_glue_obs(filename, flows):
    '''
    write the GLUE_Obs.dat
    '''
    
    with open(filename, 'w') as f:
        f.write('number\tdata\n')
        
        for k, v in flows.items():
            v.iloc[:, -1].to_csv(f, sep='\t', index=True, header=False, line_terminator='\n')
            

def write_var_file_name(filename, rchs):
    '''
    write var_file.rch
    '''
    with open(filename, 'w') as f:
       
        for i in rchs:
            f.write('FLOW_OUT_{}.txt\n'.format(i))        
#%%
                        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create streamflow calibration file for SWAT-CUP')
    parser.add_argument('TxtInOut', help='TxtInOut directory path, required.')
    parser.add_argument('output',    default='swatcup.flow', metavar='output_file', help='Output directory for plots (default: %(default)s).')
    parser.add_argument('subbasin',  default=[1], type=int,  nargs='*', help='Desired subbasin index/indices to save (default: %(default)s).')
    parser.add_argument('-l', '--log', action='store_true',  default=False, help='Prefix for plot file names')
    parser.add_argument('--usgs', nargs='*', help='The USGS site numbers for each reach')
    parser.add_argument('--weight', nargs='*', type=float,   default=[1.0], help='weight of the streamflow for each site in the objective function')
    parser.add_argument('--obcsv', nargs='*', help='The observation CSV file is the USGS station is not given')
    parser.add_argument('--iprint', type=int,   default=1, help='print code (month, day, year)')
    parser.add_argument('--nyskip', type=int,   default=2, help='number of years to skip output printing/summarization')
    parser.add_argument('-n', type=int,   default=100, metavar='minimum_number_record', help='The minimum observation record number of a gauge. \
                        If the number of record during the output period is smaller than this number, the usgs site will not included in the plot. (default: %(default)s).')


        
    
    # parser.print_help()
    # args = parser.parse_args('D:\\WorkSync\\hydrology_swat_lab\\LittleCreek1\\Scenarios\\Default\\TxtInOut  SwatCup 3 10 --usgs 07325840 07325850 -n 100 --iprint 0'.split())
    
    args = parser.parse_args()
        
    # print(args)
    if args.usgs is not None:
        assert len(args.subbasin) == len(args.usgs), 'The stat method numbers need to match the variale number.'

    # read the output.rch file:
    swatreader = swat_reader(args.TxtInOut)

    CF2CM = 0.0283168
    
    start_date = pd.Timestamp('{}-01-01'.format(int(swatreader.cio["IYR"])+int(args.nyskip))) + \
                         pd.Timedelta(0 if args.nyskip>0 else int(swatreader.cio["IDAF"]) - 1, 'D')
    end_date   = pd.Timestamp('{}-01-01'.format(int(swatreader.cio["IYR"])+int(swatreader.cio["NBYR"])-1)) + \
                             pd.Timedelta(int(swatreader.cio["IDAL"]) -1, 'D')
                             
    if not end_date.is_year_end:
        end_date = pd.Timestamp('{}-12-31'.format(int(swatreader.cio["IYR"])+int(swatreader.cio["NBYR"])-2))
    
    # get subbasin number 
    nsub = np.count_nonzero(np.char.count(os.listdir(args.TxtInOut), '.sub')) - 1

    weight = list(args.weight)
    if len(weight) == 1:
        weight = weight * len(args.subbasin)
    
    ob = OrderedDict()
    for s, u, w in zip(args.subbasin, args.usgs, weight):

        # read flow
        flow, gauge_names  = read_usgs_flow([u], '{:%Y-%m-%d}'.format(start_date), '{:%Y-%m-%d}'.format(end_date), 'D')
        flow = flow.iloc[:, 1]
        flow.index = pd.DatetimeIndex(flow.index)
        if args.iprint == 0: # monthly output
            flow = pd.to_numeric(flow).resample('M').mean()
        elif args.iprint == 1:
            pass
        elif args.iprint == 2:
            raise NotImplementedError('IPRINT is {} for annual output.\nPlotting annual output is not supported.'.format(args.iprint))
        
        
            
        flow = pd.to_numeric(flow, errors='coerce') * CF2CM
        flow.dropna(inplace=True)
        
        observed = flow.reset_index()
        observed.index += 1
        observed.iloc[:,0] = (observed.iloc[:, 0]).apply(lambda x: 'FLOW_OUT_{:%y%m%d}'.format(x))
        observed.weight = w
        ob[s] = observed
    
    if not os.path.exists(args.output):
        os.mkdir(args.output)
        
    write_observed_rch(os.path.join(args.output, 'Observed_rch.txt'), ob)
    write_observed_txt(os.path.join(args.output, 'Observed.txt'), ob)
    write_var_file_rch(os.path.join(args.output, 'Var_file_rch.txt'), args.subbasin)
    write_extract_rch( os.path.join(args.output, 'SUFI2_Extract_Rch.txt'), args.subbasin, swatreader, nsub, start_date, end_date, args.iprint)
    #write_glue_obs(os.path.join(args.output, 'GLUE_Obs.dat'), ob)
    write_var_file_name(os.path.join(args.output, 'Var_file_name.txt'), args.subbasin)
    
    
    print('\n\nSWAT-CUP calibration files are saved at {}'.format(os.path.abspath(args.output)))
   