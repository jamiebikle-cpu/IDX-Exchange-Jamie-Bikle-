# -*- coding: utf-8 -*-
"""
Created on Thu Apr  2 13:32:04 2026

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


# %% weeks 2-3

print(listing.shape)         
print(listing.dtypes)         
print(listing.isnull().sum()) 

missing = listing.isnull().sum()
missing_pct = (missing / len(listing)) * 100
missing_report = pd.DataFrame({
    "missing_count": missing, 
    "missing_pct": missing_pct
  }).sort_values("missing_pct", ascending=False)
print(missing_report)

high_missing = missing_report[missing_report['missing_pct'] > 90]
print('\nColumns above 90% missing:')
print(high_missing)



listing = listing.drop(columns=['TaxYear', 'FireplacesTotal', 'TaxAnnualAmount', 'AboveGradeFinishedArea',
    'ElementarySchoolDistrict', 'BusinessType', 'CoveredSpaces',
    'MiddleOrJuniorSchoolDistrict', 'BelowGradeFinishedArea',
    'LotSizeDimensions', 'BuilderName', 'BuildingAreaTotal',
    'CoBuyerAgentFirstName'])

print(f'Columns remaining after drop: {listing.shape[1]}')

dist_cols = ["ClosePrice", "ListPrice", "OriginalListPrice", "LivingArea",
"LotSizeAcres", "BedroomsTotal", "BathroomsTotalInteger", "DaysOnMarket", "YearBuilt"]

print(listing[dist_cols].describe(percentiles=[.1,.25,.5,.75,.9]))


for col in dist_cols:
    plt.figure()
    listing[col].hist(bins=50)
    plt.title(f"Histogram: {col}")
    plt.xlabel(col)
    plt.ylabel('Count')
    plt.tight_layout()
    plt.show()


for col in dist_cols:
    plt.figure()
    listing[col].dropna().plot(kind='box')
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

listing['year_month'] = pd.to_datetime(listing["ListingContractDate"]).dt.to_period('M')

listing_with_rates = listing.merge(mortgage_monthly, on="year_month", how="left")

print(listing_with_rates[["ListingContractDate", "year_month", "ListPrice",
"rate_30yr_fixed"]].head())

print(f'Null rates after merge: {listing_with_rates["rate_30yr_fixed"].isnull().sum()}')
listing_with_rates.to_csv('idxex/listing_with_rates.csv', index=False)
print('Saved: idxex/listing_with_rates.csv')

# %% weeks 4-5
listing_with_rates["CloseDate"] = pd.to_datetime(listing_with_rates["CloseDate"])
listing_with_rates["PurchaseContractDate"] = pd.to_datetime(listing_with_rates["PurchaseContractDate"])
listing_with_rates["ListingContractDate"] = pd.to_datetime(listing_with_rates["ListingContractDate"])
listing_with_rates["ListingContractDate"] = pd.to_datetime(listing_with_rates["ListingContractDate"])               
listing_with_rates["ContractStatusChangeDate"] = pd.to_datetime(listing_with_rates["ContractStatusChangeDate"])               




listing_with_rates["listing_after_close_flag"] = listing_with_rates["ListingContractDate"] > listing_with_rates["CloseDate"]
listing_with_rates["purchase_after_close_flag"] = listing_with_rates["PurchaseContractDate"] > listing_with_rates["CloseDate"]

listing_with_rates["negative_timeline_flag"] = (
    listing_with_rates["listing_after_close_flag"] |
    listing_with_rates["purchase_after_close_flag"] |
    (listing_with_rates["ListingContractDate"] > listing_with_rates["PurchaseContractDate"])
)
                   

listing_with_rates["ClosePrice_flag"] = listing_with_rates["ClosePrice"] <= 0
listing_with_rates["LivingArea_flag"] = listing_with_rates["LivingArea"] <= 0
listing_with_rates["DaysOnMarket_flag"] = listing_with_rates["DaysOnMarket"] < 0
listing_with_rates["BedroomsTotal_flag"] = listing_with_rates["BedroomsTotal"] < 0
listing_with_rates["BathroomsTotalInteger_flag"] = listing_with_rates["BathroomsTotalInteger"] < 0

listing_with_rates["Latitude_missing_flag"] = listing_with_rates["Latitude"].isnull()
listing_with_rates["Longitude_missing_flag"] = listing_with_rates["Longitude"].isnull()

listing_with_rates["Latitude_zero_flag"] = listing_with_rates["Latitude"] == 0
listing_with_rates["Longitude_zero_flag"] = listing_with_rates["Longitude"] == 0

listing_with_rates["Longitude_positive_flag"] = listing_with_rates["Longitude"] > 0

listing_with_rates["Latitude_state_flag"] = (
    (listing_with_rates["Latitude"] < 32.5) |
    (listing_with_rates["Latitude"] > 42) |
    (listing_with_rates["Longitude"] < -124.5) |
    (listing_with_rates["Longitude"] > -114)
)

listing_with_rates.to_csv('idxex/listing_with_flags.csv', index=False)

print(f'listing_after_close_flag: {listing_with_rates["listing_after_close_flag"].sum()}')
print(f'purchase_after_close_flag: {listing_with_rates["purchase_after_close_flag"].sum()}')
print(f'negative_timeline_flag: {listing_with_rates["negative_timeline_flag"].sum()}')
print(f'ClosePrice_flag: {listing_with_rates["ClosePrice_flag"].sum()}')
print(f'LivingArea_flag: {listing_with_rates["LivingArea_flag"].sum()}')
print(f'DaysOnMarket_flag: {listing_with_rates["DaysOnMarket_flag"].sum()}')
print(f'BedroomsTotal_flag: {listing_with_rates["BedroomsTotal_flag"].sum()}')
print(f'BathroomsTotalInteger_flag: {listing_with_rates["BathroomsTotalInteger_flag"].sum()}')
print(f'Latitude_missing_flag: {listing_with_rates["Latitude_missing_flag"].sum()}')
print(f'Longitude_missing_flag: {listing_with_rates["Longitude_missing_flag"].sum()}')
print(f'Latitude_zero_flag: {listing_with_rates["Latitude_zero_flag"].sum()}')
print(f'Longitude_zero_flag: {listing_with_rates["Longitude_zero_flag"].sum()}')
print(f'Longitude_positive_flag: {listing_with_rates["Longitude_positive_flag"].sum()}')
print(f'out_of_state_flag: {listing_with_rates["Latitude_state_flag"].sum()}')

