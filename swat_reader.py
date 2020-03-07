# -*- coding: utf-8 -*-
"""
This script read SWAT output data.

Created on Fri Feb 14 00:21:31 2020

@author: Michael Ou

usage:
    python swat_plot.py 
"""


import os
import pandas as pd
import numpy as np
import datetime
#%% SWAT_reader class
class swat_reader():
    
    def __init__(self, TxtInOut):
        self.TxtInOut = TxtInOut
        self.read_cio()
    
    def __repr__(self):
        return 'SWAT Model at {}'.format(self.TxtInOut)
        
    def read_cio(self,):
        '''
        read SWAT file.cio

        Returns
        -------
        None.

        '''
        self.cio = dict()
        lines_to_skip = tuple(range(7)) + (11, 33) + tuple(range(33, 41)) + (45, 47, 53, 57) + tuple(range(62, 73)) + (77, )
        with open(os.path.join(self.TxtInOut, 'file.cio')) as f:
            for i, l in enumerate(f):
                if i in lines_to_skip:
                    continue
                else:
                    val, key = l.split('|')
                    key = key[:key.index(':')].strip()
                    self.cio[key] = val.strip()
        
        
        # self.output_start_date = pd.DateOffset(pd.Timestamp('{}-01-01'.format(int(self.cio["IYR"])+int(self.cio["NYSKIP"]))), day=int(self.cio["IDAF"])-1)
        # self.output_end_date   = pd.DateOffset(pd.Timestamp('{}-01-01'.format(int(self.cio["IYR"])+int(self.cio["NBYR"])-1)), day=int(self.cio["IDAL"])-1)       
    
        self.output_start_date = pd.Timestamp('{}-01-01'.format(int(self.cio["IYR"])+int(self.cio["NYSKIP"]))) + \
                                 pd.Timedelta(0 if self.cio["NYSKIP"]>'0' else int(self.cio["IDAF"]) - 1, 'D')
        self.output_end_date   = pd.Timestamp('{}-01-01'.format(int(self.cio["IYR"])+int(self.cio["NBYR"])-1)) + \
                                 pd.Timedelta(int(self.cio["IDAL"]) -1, 'D')
    
    def read_input_sub(self):
        TxtInOut = self.TxtInOut
        
        with open(os.path.join(TxtInOut, 'fig.fig')) as fig:
            figlines = fig.readlines()
            
        isub = 0
        subhru = []
        for i in np.nonzero(map(lambda x: 'subbasin' in x, figlines))[0] + 1:
            isub += 1
            with open(os.path.join(TxtInOut, figlines[i].strip())) as fsub:
                sublines = fsub.readlines()
                
            
            sub_area = float(sublines[1][:20])
            ih = np.nonzero(map(lambda x: x.startswith('HRU: General'), sublines))[0][0]
            
            for ihru, l in enumerate(sublines[ih+1:]):
                hru_val = [isub, ihru+1, sub_area]
                
                with open(os.path.join(TxtInOut, l[:13])) as fhru:
                    hrulines = fhru.readlines()
                    l0 = hrulines[0]
                    hru_val.append(l0[l0.index('Luse:')+5:l0.index('Luse:')+10].strip())
                    hru_val.append(l0[l0.index('Soil:')+5:l0.index('Soil:')+12].strip())
                    hru_val.append(l0[l0.index('Slope:')+6:l0.index('Slope:')+14].strip())
                    hru_val.append(float(hrulines[1][:20])) # frac
                    hru_val.append(float(hrulines[4][:20])) # ov_n
                    hru_val.append(float(hrulines[8][:20])) # canmx
            
                with open(os.path.join(TxtInOut, l[13:26])) as fhru:
                    hrulines = fhru.readlines()
                    hru_val.append(float(hrulines[10][:20])) # cn2
                    hru_val.append(float(hrulines[11][:20])) # usle_p
                    
                    
                subhru.append(hru_val)
                    
        self.subhru = pd.DataFrame(subhru, columns=['subbasin', 'hru', 'subarea', 'landuse', 'soil', 'slope', 'frac', 'ov_n', 'canmx', 'cn2', 'usle_p'])
    
    
    def write_input_sub(self, subhru):
        TxtInOut = self.TxtInOut
        
        with open(os.path.join(TxtInOut, 'fig.fig')) as fig:
            figlines = fig.readlines()
            
        isub = 0
        subfiles = np.array(figlines)[np.nonzero(map(lambda x: 'subbasin' in x, figlines))[0] + 1]
        subfiles = np.char.strip(subfiles)
        
            
            
        for isub, df_hru in subhru.groupby('subbasin'):
#            print(isub)
            with open(os.path.join(TxtInOut, subfiles[isub - 1])) as fsub:
                sublines = fsub.readlines()
                ih = np.nonzero(map(lambda x: x.startswith('HRU: General'), sublines))[0][0]
            
            for ihru, r in df_hru.reset_index().iterrows():
                l = sublines[ih +ihru + 1]
                                
                with open(os.path.join(TxtInOut, l[:13])) as fhru:
                    hrulines = fhru.readlines()
                
                hrulines[1] = '{:<20}'.format(r.frac) + '| frac\n'
                hrulines[4] = '{:<20}'.format(r.ov_n) + '| ov_n\n'
                hrulines[8] = '{:<20}'.format(r.canmx) + '| canmx\n'
                
                with open(os.path.join(TxtInOut, l[:13]), 'w') as fhru:
                    fhru.writelines(hrulines)
            
                with open(os.path.join(TxtInOut, l[13:26])) as fhru:
                    hrulines = fhru.readlines()
                
                hrulines[10] = '{:<20}'.format(r.cn2) + '| cn2\n'
                hrulines[11] = '{:<20}'.format(r.usle_p) + '| usle_p\n'                
                
                with open(os.path.join(TxtInOut, l[13:26]), 'w') as fhru:
                    fhru.writelines(hrulines)
                    
        
    def read_sub(self):
        '''
        read SWAT output sub

        Returns
        -------
        None.

        '''
        
    
        self.sub = dict()
        
        with open(os.path.join(self.TxtInOut, 'output.sub')) as f:
            for l in f:
                if l.startswith('HRU: General'):
                    break
                
            for l in f:
                self.sub
            
        return lines
            
    
    
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
                                                                          
        widths = [6, 5, 10, 3, 3, 5, 13] if self.cio['ICALEN'] == '1' else [6, 5, 9, 6, 12]
        return cols_first + [c.strip() for c in columns], widths + [12] * len(columns)
        
    def read_rch(self):
        '''
        read SWAT output reach

        Returns
        -------
        dat : TYPE
            DESCRIPTION.

        '''
        fpath = os.path.join(self.TxtInOut, 'output.rch')
        
        assert os.path.exists(fpath), '{} does not exist. Make sure the model run has completed.'.format(fpath)
        
        with open(fpath) as f:
            columns, widths = self.get_rch_header_width()
            dat = pd.read_fwf(f, skiprows=9, header=None, widths=widths)
            dat.columns = columns
            if self.cio['ICALEN'] == '1': 
                dat.index = dat.apply(lambda x: datetime.datetime(x.YR, x.MO, x.DA), axis=1)
            else:
                # TODO: may need to change if the starting date is not Januray 1
                step = {'0':'M', '1':'D', '2':'A'}
                nsub = dat.RCH.max()
                dat = dat[dat.MON <= 366] # remove the annual output
                if self.cio['IPRINT'] == '0': # remove the ending statistics for monthly output
                    dat = dat.iloc[:-nsub]                    
                date_index = pd.date_range(self.output_start_date, self.output_end_date, freq=step[self.cio['IPRINT']])
                dat.index = np.repeat(date_index, nsub)
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
#%%    
if __name__ == '__main__':
    TxtInOut = r"D:\WorkSync\hydrology_swat_lab\LittleCreek1\Scenarios\Default\TxtInOut"   
    swatreader = swat_reader(TxtInOut)
    swatreader.cio['IPRINT']
    
    df_out = swatreader.read_rch()
