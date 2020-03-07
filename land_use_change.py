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
import pandas as pd
import os
#%% set up the command
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Read and write SWAT HRU fractions or/and parameter values')
    parser.add_argument('TxtInOut', help='TxtInOut directory path, required.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-r', '--read',  action='store_true', default=False, help='read parameters from the SWAT model files')
    group.add_argument('-w', '--write', action='store_true', default=False, help='write parameters to the SWAT model files')
    parser.add_argument('-f', '--file', default='swat_landuse.csv', type=str, help='csv file to read or save ')
   
    
    # parser.print_help()
    # args = parser.parse_args(r'D:\WorkSync\hydrology_swat_lab\LittleCreek1\Scenarios\Default\TxtInOut -r '.split())
    
    args = parser.parse_args()
    
    
    # print(args)
    
    if not os.path.exists(args.TxtInOut):
        raise OSError(args.TxtInOut + ' not found')
    
    # read the output.rch file:
    swatreader = swat_reader(args.TxtInOut)    
    
    if args.write:
        if not os.path.exists(args.file):
            raise OSError(args.file + ' not found')
            
        subhru = pd.read_csv(args.file)
        subhru.loc[0, 'cn2'] = 100
        swatreader.write_input_sub(subhru)
        
        print('Parameter data have been successfully written to model input files at {}'.format(args.TxtInOut))
    
    else:
        # read parameter from model files
        swatreader.read_input_sub()
        swatreader.subhru.to_csv(args.file, index=False)
    # change temperature data
    
        print('Parameter data have been successfully saved to {}'.format(args.file))