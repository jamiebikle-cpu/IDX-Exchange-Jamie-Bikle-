# -*- coding: utf-8 -*-
"""
Created on Thu Apr  2 13:32:04 2026

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
    filename = f'CRMLSListing{year}{month:02d}.csv'
    filepath = os.path.join(data_folder, filename)
    if os.path.exists(filepath):
        df_month = pd.read_csv(filepath, low_memory=False)
        months.append(df_month)
        print(f'Loaded: {filename}({len(df_month)} rows)')
    else:
        print(f'File not found - {filename}')

listing = pd.concat(months, ignore_index=True)
print(f'\nRow count after concatenation" {len(listing)}')   

print(f'\nRow count after concatenation" {len(listing)}') 
print(listing['PropertyType'].value_counts()) 

listing = listing[listing['PropertyType'] == 'Residential']
print(f'Row count after residential filter: {len(listing)}')

print(listing['PropertyType'].value_counts())


listing.to_csv('idxex/listing_combined.csv', index = False) 
print('Saved: idxex/listing_combined.csv')
