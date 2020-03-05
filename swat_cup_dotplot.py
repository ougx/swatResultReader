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
import os
import matplotlib.pyplot as plt


print(plt.style.available)
plt.style.use('fivethirtyeight')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create dot plots of SWAT-CUP calibration')
    parser.add_argument('goalfile', help='The file path to goal.txt, required.')
    parser.add_argument('-o', '--output',  default='.', metavar='output_dir', help='Output directory for plots (default: %(default)s).')
    parser.add_argument('-p', '--prefix',  default='', help='Prefix for plot file names')

        
    
    # parser.print_help()
    # args = parser.parse_args(r'F:\Work\LittleCr.Sufi2.SwatCup\Iterations\Iter1\Sufi2.Out\goal.txt'.split())
    
    args = parser.parse_args()
        
    output_dir = args.output
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
        
    # read the output.rch file:
    goal = pd.read_csv(args.goalfile, sep=' ', index_col=0, skipinitialspace=True, skiprows=3)
    
    for i in range(goal.shape[1] - 1):
        parname = goal.iloc[:, i].name
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.scatter(goal.iloc[:, i], goal['goal_value'], s=10)
        ax.set_xlabel(parname)
        ax.set_ylabel('Objective function')
        fig.savefig(os.path.join(output_dir, '{}{}.png'.format(args.prefix, parname.replace(':', '_'))), dpi=300, bbox_inches='tight')
        