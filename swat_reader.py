# -*- coding: utf-8 -*-
"""
This script read SWAT output data.

Created on Fri Feb 14 00:21:31 2020

@author: Michael Ou

usage:
    python swat_plot.py 
"""


TxtInOut = r'D:\WorkSync\CPNRD-UnSWAT\ArcSWAT_2021\Scenarios\Default-Irrigation\TxtInOut'


import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from urllib.request import urlopen
import datetime
#%% SWAT_reader class
class swat_reader():
    
    def __init__(self, TxtInOut):
        self.TxtInOut = TxtInOut
        self.read_cio()
    
    def __repr__(self):
        return f'SWAT Model at {self.TxtInOut}'
        
    def read_cio(self,):
        '''
        read SWAT file.cio

        Returns
        -------
        None.

        '''
        self.cio = dict()
        lines_to_skip = tuple(range(7)) + (11, 33) + tuple(range(33, 41)) + (45, 47, 53, 57) + tuple(range(62, 73)) + (77, )
        with open(os.path.join(TxtInOut, 'file.cio')) as f:
            for i, l in enumerate(f):
                if i in lines_to_skip:
                    continue
                else:
                    val, key = l.split('|')
                    key = key[:key.index(':')].strip()
                    self.cio[key] = val.strip()
    
    
    def read_sub(self):
        '''
        read SWAT output sub

        Returns
        -------
        None.

        '''
        with open(os.path.join(self.TxtInOut, 'output.sub')) as f:
            pass
            
    
    
    def get_rch_header_width(self):
        """
        Check ICALEN: Code for printing out calendar or julian dates to .rch, .sub and .hru files

        Returns
        -------
        column names for output.sub

        """
        columns= ["  FLOW_INcms"," FLOW_OUTcms","     EVAPcms",            
                  "    TLOSScms","  SED_INtons"," SED_OUTtons",            
                  "SEDCONCmg/kg","   ORGN_INkg","  ORGN_OUTkg",            
                  "   ORGP_INkg","  ORGP_OUTkg","    NO3_INkg",            
                  "   NO3_OUTkg","    NH4_INkg","   NH4_OUTkg",            
                  "    NO2_INkg","   NO2_OUTkg","   MINP_INkg",            
                  "  MINP_OUTkg","   CHLA_INkg","  CHLA_OUTkg",            
                  "   CBOD_INkg","  CBOD_OUTkg","  DISOX_INkg",            
                  " DISOX_OUTkg"," SOLPST_INmg","SOLPST_OUTmg",            
                  " SORPST_INmg","SORPST_OUTmg","  REACTPSTmg",          
                  "    VOLPSTmg","  SETTLPSTmg","RESUSP_PSTmg",            
                  "DIFFUSEPSTmg","REACBEDPSTmg","   BURYPSTmg",            
                  "   BED_PSTmg"," BACTP_OUTct","BACTLP_OUTct",            
                  "  CMETAL#1kg","  CMETAL#2kg","  CMETAL#3kg",            
                  "     TOT Nkg","     TOT Pkg"," NO3ConcMg/l",            
                  "    WTMPdegc"]
        cols_first = 'TYPE RCH GIS MO DA YR AREAkm2'.split() if self.cio['ICALEN'] == '1' else 'TYPE RCH GIS MON AREAkm2'.split()
                                                                          
        widths = [6, 5, 10, 3, 3, 5, 13] if self.cio['ICALEN'] == '1' else [6, 4, 9, 6, 12]
        return cols_first + [c.strip() for c in columns], widths + [12] * len(columns)
        
    def read_rch(self):
        '''
        read SWAT output reach

        Returns
        -------
        dat : TYPE
            DESCRIPTION.

        '''
        with open(os.path.join(self.TxtInOut, 'output.rch')) as f:
            columns, widths = self.get_rch_header_width()
            dat = pd.read_fwf(f, skiprows=9, header=None, widths=widths, columns=columns)
            dat.columns = columns
            if self.cio['ICALEN'] == '1': 
                dat.index = dat.apply(lambda x: datetime.datetime(x.YR, x.MO, x.DA), axis=1)
            else:
                # TODO: may need to change if the starting date is not Januray 1
                start_date = pd.DateOffset(pd.Timestamp(f'{int(self.cio["IYR"])+int(self.cio["NYSKIP"])}-01-01'), day=int(self.cio["IDAF"])-1)
                end_date   = pd.DateOffset(pd.Timestamp(f'{int(self.cio["IYR"])+int(self.cio["NBYR"])-1}-01-01'), day=int(self.cio["IDAL"])-1)
                step = {'0':'M', '1':'D', '2':'A'}
                dat.index = np.tile(pd.date_range(start_date, end_date, freq=step[self.cio['IPRINT']]), )
                dat.index.name = 'time'
        return dat.iloc[:, [1] + list(range(columns.index('AREAkm2')+1, len(columns)))]
    
    
    @staticmethod
    def filter(df_out, units, vars, freq=None, stat=None):
        '''
        

        Parameters
        ----------
        df_out : TYPE
            the raw dataframe of a SWAT output file 
        units : TYPE
            the unit (hru, sub or rch) to be keep.
        vars : TYPE
            the variables to be keep.

        Returns
        -------
        filtered dataframe.

        '''
        unit = df_out.columns[0]
        df_filter = df_out.loc[df_out[unit].isin(units), [unit] + vars]
    
        if freq is not None:
            # do aggregation
            df_filter = df_filter.groupby(unit).resample(freq).agg({k:v for k, v in zip( vars, stat)})
            df_filter.index.names = [unit, 'time']
        else:
            # reorder to make output consistent with aggreation
            df_filter.index.name = 'time'
            df_filter = df_filter.reset_index().set_index([unit, 'time']).sort_index()
            
        return df_filter