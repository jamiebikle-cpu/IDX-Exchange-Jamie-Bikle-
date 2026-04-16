# -*- coding: utf-8 -*-
"""
Created on Wed Apr  1 23:11:00 2026

@author: jgbik
"""

import pandas as pd
import os
import matplotlib.pyplot as plt


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


print(sold.shape)         
print(sold.dtypes)         
print(sold.isnull().sum()) 

missing = sold.isnull().sum()
missing_pct = (missing / len(sold)) * 100
missing_report = pd.DataFrame({
    "missing_count": missing, 
    "missing_pct": missing_pct
  }).sort_values("missing_pct", ascending=False)
print(missing_report)

high_missing = missing_report[missing_report['missing_pct'] > 90]
print('\nColumns above 90% missing:')
print(high_missing)



sold = sold.drop(columns=['TaxYear', 'FireplacesTotal', 'TaxAnnualAmount', 'AboveGradeFinishedArea',
    'ElementarySchoolDistrict', 'BusinessType', 'CoveredSpaces',
    'MiddleOrJuniorSchoolDistrict', 'WaterfrontYN', 'BelowGradeFinishedArea',
    'BasementYN', 'LotSizeDimensions', 'BuilderName', 'BuildingAreaTotal',
    'CoBuyerAgentFirstName', 'OriginatingSystemSubName', 'OriginatingSystemName'])

print(f'Columns remaining after drop: {sold.shape[1]}')

dist_cols = ["ClosePrice", "ListPrice", "OriginalListPrice", "LivingArea",
"LotSizeAcres", "BedroomsTotal", "BathroomsTotalInteger", "DaysOnMarket", "YearBuilt"]

print(sold[dist_cols].describe(percentiles=[.1,.25,.5,.75,.9]))


for col in dist_cols:
    plt.figure()
    sold[col].hist(bins=50)
    plt.title(f"Histogram: {col}")
    plt.xlabel(col)
    plt.ylabel('Count')
    plt.tight_layout()
    plt.show()


for col in dist_cols:
    plt.figure()
    sold[col].dropna().plot(kind='box')
    plt.title(f'Boxplot: {col}')
    plt.tight_layout()
    plt.show()
    
url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US"
mortgage = pd.read_csv(url)
mortgage.columns = ["date", "rate_30yr_fixed"]

mortgage["date"] = pd.to_datetime(mortgage['date'])

mortgage['year_month'] = mortgage['date'].dt.to_period('M')

mortgage_monthly = (
 mortgage.groupby("year_month")["rate_30yr_fixed"]
 .mean().reset_index()
)

sold['year_month'] = pd.to_datetime(sold['CloseDate']).dt.to_period('M')

sold_with_rates = sold.merge(mortgage_monthly, on="year_month", how="left")

print(sold_with_rates[["CloseDate", "year_month", "ClosePrice",
"rate_30yr_fixed"]].head())

print(f'Null rates after merge: {sold_with_rates["rate_30yr_fixed"].isnull().sum()}')
sold_with_rates.to_csv('idxex/sold_with_rates.csv', index=False)
print('Saved: idxex/sold_with_rates.csv')

