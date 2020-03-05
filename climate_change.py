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
import shutil
import numpy as np
#%% set up the command
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Save desired resultd from SWAT output.rch to a CSV file')
    parser.add_argument('TxtInOut', help='TxtInOut directory path, required.')
    parser.add_argument('-t', '--temperature',    default=0.0, type=float, help='temperature difference.')
    parser.add_argument('-p', '--precipitation',  default=1.0, type=float, help='relative precipitation change')
   
    
    # parser.print_help()
    # args = parser.parse_args(r'D:\WorkSync\hydrology_swat_lab\LittleCreek1\Scenarios\Default\TxtInOut'.split())
    
    args = parser.parse_args()
    
    
    # print(args)
    
    if not os.path.exists(args.TxtInOut):
        raise OSError(args.TxtInOut + ' not found')
    
    # read the output.rch file:
    swatreader = swat_reader(args.TxtInOut)    
    
    # change temperature data
    shutil.copy2(os.path.join(args.TxtInOut, 'pcp1.pcp'), os.path.join(args.TxtInOut, 'pcp1.pcp.bak'))
    shutil.copy2(os.path.join(args.TxtInOut, 'Tmp1.Tmp'), os.path.join(args.TxtInOut, 'Tmp1.Tmp.bak'))
    
    if args.temperature != 0.0:
        with open(os.path.join(args.TxtInOut, 'Tmp1.Tmp.bak')) as fr:  
            with open(os.path.join(args.TxtInOut, 'Tmp1.Tmp'), 'w') as fw:
                # write headers
                l = fr.readline()
                nsite = l.count(',')
                fw.write(l)
                for i in range(3):
                    l = fr.readline()
                    fw.write(l)
                data = pd.read_fwf(fr, widths=[7] + nsite * 2 * [5], header=None)
                # make changes                
                data.iloc[:, 1:] = data.iloc[:, 1:] + args.temperature
                #fw.write(data.to_string(index=False, header=False, float_format='%5.1f', col_space=0))
                np.savetxt(fw, data.values, fmt='%7.0f' + '%5.1f' * nsite * 2)
                    
                
    if args.precipitation != 1.0:
        with open(os.path.join(args.TxtInOut, 'pcp1.pcp.bak')) as fr:  
            with open(os.path.join(args.TxtInOut, 'pcp1.pcp'), 'w') as fw:
                # write headers
                l = fr.readline()
                nsite = l.count(',')
                fw.write(l)
                for i in range(3):
                    l = fr.readline()
                    fw.write(l)
                data = pd.read_fwf(fr, widths=[7] + nsite * [5], header=None)
                # make changes                
                data.iloc[:, 1:] = data.iloc[:, 1:] * args.precipitation
                #fw.write(data.to_string(index=False, header=False, float_format='%5.1f', col_space=0))
                np.savetxt(fw, data.values, fmt='%7.0f' + '%5.1f' * nsite)
      
    
    print('Climate data have been successfully changed')
