# -*- coding: utf-8 -*-
"""
Created on Wed Apr  1 23:11:00 2026

@author: jgbik
"""

import pandas as pd
import os
import matplotlib.pyplot as plt



# %% week 1
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



# %% weeks 2-3
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


# %% weeks 4-5

#convert to datetime
sold_with_rates["CloseDate"] = pd.to_datetime(sold_with_rates["CloseDate"])
sold_with_rates["PurchaseContractDate"] = pd.to_datetime(sold_with_rates["PurchaseContractDate"])
sold_with_rates["ListingContractDate"] = pd.to_datetime(sold_with_rates["ListingContractDate"])
sold_with_rates["ListingContractDate"] = pd.to_datetime(sold_with_rates["ListingContractDate"])               
sold_with_rates["ContractStatusChangeDate"] = pd.to_datetime(sold_with_rates["ContractStatusChangeDate"])               



#flags where timeline is not in chronological order
#for example, a listing cannot be created after it closes/is under contract
sold_with_rates["listing_after_close_flag"] = sold_with_rates["ListingContractDate"] > sold_with_rates["CloseDate"]
sold_with_rates["purchase_after_close_flag"] = sold_with_rates["PurchaseContractDate"] > sold_with_rates["CloseDate"]
sold_with_rates["negative_timeline_flag"] = (
    sold_with_rates["listing_after_close_flag"] |
    sold_with_rates["purchase_after_close_flag"] |
    (sold_with_rates["ListingContractDate"] > sold_with_rates["PurchaseContractDate"])
)
                   

#flags impossible values
sold_with_rates["ClosePrice_flag"] = sold_with_rates["ClosePrice"] <= 0
sold_with_rates["LivingArea_flag"] = sold_with_rates["LivingArea"] <= 0
sold_with_rates["DaysOnMarket_flag"] = sold_with_rates["DaysOnMarket"] < 0
sold_with_rates["BedroomsTotal_flag"] = sold_with_rates["BedroomsTotal"] < 0
sold_with_rates["BathroomsTotalInteger_flag"] = sold_with_rates["BathroomsTotalInteger"] < 0

#missing coordinates
sold_with_rates["Latitude_missing_flag"] = sold_with_rates["Latitude"].isnull()
sold_with_rates["Longitude_missing_flag"] = sold_with_rates["Longitude"].isnull()

#flags lat/lon = 0 
sold_with_rates["Latitude_zero_flag"] = sold_with_rates["Latitude"] == 0
sold_with_rates["Longitude_zero_flag"] = sold_with_rates["Longitude"] == 0

#flags if positive longitude as all ca properties have negative lon
sold_with_rates["Longitude_positive_flag"] = sold_with_rates["Longitude"] > 0

#flags out of state coordinates
sold_with_rates["Latitude_state_flag"] = (
    (sold_with_rates["Latitude"] < 32.5) |
    (sold_with_rates["Latitude"] > 42) |
    (sold_with_rates["Longitude"] < -124.5) |
    (sold_with_rates["Longitude"] > -114)
)


sold_with_rates.to_csv('idxex/sold_with_flags.csv', index=False)


flag_cols = [
    'listing_after_close_flag', 'purchase_after_close_flag', 'negative_timeline_flag',
    'ClosePrice_flag', 'LivingArea_flag', 'DaysOnMarket_flag',
    'BedroomsTotal_flag', 'BathroomsTotalInteger_flag',
    'Latitude_missing_flag', 'Longitude_missing_flag',
    'Latitude_zero_flag', 'Longitude_zero_flag',
    'Longitude_positive_flag', 'Latitude_state_flag'
]

for flag in flag_cols:
    print(f'{flag}: {sold_with_rates[flag].sum()}')
    
# geographic data quality summary
invalid_coords = sold_with_rates[
    sold_with_rates["Latitude_missing_flag"] |
    sold_with_rates["Longitude_missing_flag"] |
    sold_with_rates["Latitude_zero_flag"] |
    sold_with_rates["Longitude_zero_flag"] |
    sold_with_rates["Longitude_positive_flag"] |
    sold_with_rates["Latitude_state_flag"]
]
print(f'\nTotal records with invalid coordinates: {len(invalid_coords)}')
print(f'As a percentage of total records: {len(invalid_coords) / len(sold_with_rates) * 100:.2f}%')