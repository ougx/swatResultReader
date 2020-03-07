# -*- coding: utf-8 -*-
"""
This script read a SWAT output.rch file and save to csv file.

Created on Fri Feb 14 00:21:31 2020

@author: Michael Ou

usage:
    python save_rch.py 
"""



from swat_reader import swat_reader
import argparse
import os



#%% set up the command
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Save desired resultd from SWAT output.rch to a CSV file')
    parser.add_argument('TxtInOut', help='TxtInOut directory path, required.')
    parser.add_argument('-b', '--subbasin',  default=[1], type=int,  nargs='*', help='Desired subbasin index/indices to save (default: %(default)s).')
    parser.add_argument('-v', '--variable',  default=["FLOW_OUTcms"], nargs='*', help='Desired variable to save (default: %(default)s).')
    parser.add_argument('-o', '--output',    default='rch.csv', metavar='rch.csv', help='File path of the csv to save the desired SWAT results (default: %(default)s).')
    parser.add_argument('-s', '--stat', metavar='stat_method', nargs='*', choices='sum mean std sem max min median first last'.split(), 
                        help='''
                        Calculate and save the statistics using Pandas resampling function to upscale the temporal frequency. 
                        Use -r or --resample to specify the resample frequency.
                        You can use one stat_method for all variables otherwise the number of stat_methods should equal to the number of variable to be saved.
                        Aggregating options: sum, mean, std, sem, max, min, median, first, last.                        
                        Reference: https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#resampling
                        ''')
    parser.add_argument('-f', '--freq', help='aggreation/resample frequency.')
    
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
    df_save = swat_reader.filter(df_out, args.subbasin, args.variable, args.freq, args.stat)
   
    # save the csv
    df_out.to_csv('.'.join(args.output.split('.')[:-1] + ['all','csv']))
    df_save.to_csv(args.output)
    
    
    print('Data are saved successfully at {}'.format(os.path.abspath(args.output)))