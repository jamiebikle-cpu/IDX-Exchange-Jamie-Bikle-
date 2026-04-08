# -*- coding: utf-8 -*-
"""
Created on Wed Apr  1 23:11:00 2026

@author: jgbik
"""

import pandas as pd
import os


data_folder = 'idxex'
months = []

for year in [2024, 2025, 2026]:
    if year == 2026:
        month_range = range(1,4)
        
    else:
        month_range = range(1,13)

for month in month_range:
    filename = f'CRMLSSold{year}{month:02d}.csv'
    filepath = os.path.join(data_folder, filename)
    if os.path.exists(filepath):
        df_month = pd.read_csv(filepath, low_memory=False)
        months.append(df_month)
        print(f'Loaded: {filename}({len(df_month)} rows)')
    else:
        print(f'File not found - {filename}')

sold = pd.concat(months, ignore_index=True)
print(f'\nRow count after concatenation" {len(sold)}') 
print(sold['PropertyType'].value_counts()) 

sold = sold[sold['PropertyType'] == 'Residential']
print(f'Row count after residential filter: {len(sold)}')

print(sold['PropertyType'].value_counts())

sold.to_csv('idxex/sold_combined.csv', index = False) 
print('Saved: idxex/sold_combined.csv')
