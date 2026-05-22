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
        month_range = range(1,5)
        
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

# %% week 6

#key metrics
sold_with_rates["PriceRatio"] = sold_with_rates["ClosePrice"] / sold_with_rates["OriginalListPrice"]
sold_with_rates["PricePerSqFt"] = sold_with_rates["ClosePrice"] / sold_with_rates["LivingArea"]
sold_with_rates["Year"] = sold_with_rates["CloseDate"].dt.year
sold_with_rates["Month"] = sold_with_rates["CloseDate"].dt.month
sold_with_rates["YrMo"] = sold_with_rates["CloseDate"].dt.to_period("M").astype(str)
sold_with_rates["CloseToOriginalListRatio"] = sold_with_rates["ClosePrice"] / sold_with_rates["OriginalListPrice"]
sold_with_rates["ListingToContractDays"] = (
    sold_with_rates["PurchaseContractDate"] - sold_with_rates["ListingContractDate"]
).dt.days

sold_with_rates["ContractToCloseDays"] = (
    sold_with_rates["CloseDate"] - sold_with_rates["PurchaseContractDate"]
).dt.days

#segment analysis
print(sold_with_rates.groupby("PropertySubType")["ClosePrice"].agg(["count", "mean", "median", "min", "max"]))
print(sold_with_rates.groupby("PropertyType")["ClosePrice"].agg(["count", "mean", "median", "min", "max"]))

print(sold_with_rates.groupby("CountyOrParish")["ClosePrice"].agg(["count", "mean", "median", "min", "max"]))
print(sold_with_rates.groupby("MLSAreaMajor")["ClosePrice"].agg(["count", "mean", "median", "min", "max"]))

print(sold_with_rates.groupby("ListOfficeName")["ClosePrice"].agg(["count", "mean", "median", "min", "max"]))
print(sold_with_rates.groupby("BuyerOfficeName")["ClosePrice"].agg(["count", "mean", "median", "min", "max"]))


#output table
print(sold_with_rates[['ClosePrice', 'PriceRatio', 'CloseToOriginalListRatio', 
                        'PricePerSqFt', 'DaysOnMarket', 'YrMo', 
                        'ListingToContractDays', 'ContractToCloseDays']].head(10))

#csv file
sold_with_rates.to_csv('idxex/sold_week6.csv', index=False)
print('Saved: idxex/sold_with_flags.csv')

# %% week 7

print(sold_with_rates[["ClosePrice", "LivingArea", "DaysOnMarket"]].describe(percentiles=[.01, .05, .10, .90, .95, .99]))

def iqr_func(df, col): 
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    df[col + "_outlier_flag"] = (df[col] < lower) | (df[col] > upper)
    return df

sold_with_rates = iqr_func(sold_with_rates, "ClosePrice")
sold_with_rates = iqr_func(sold_with_rates, "LivingArea")
sold_with_rates = iqr_func(sold_with_rates, "DaysOnMarket")

sold_with_rates.to_csv('idxex/sold_flagged.csv', index=False)
print('Saved: idxex/sold_flagged.csv')


sold_clean = sold_with_rates[
    (sold_with_rates["ClosePrice_outlier_flag"] == False) &
    (sold_with_rates["LivingArea_outlier_flag"] == False) &
    (sold_with_rates["DaysOnMarket_outlier_flag"] == False)
]
sold_clean.to_csv('idxex/sold_clean.csv', index=False)
print('Saved: idxex/sold_clean.csv')

print(f'Rows before outlier removal: {len(sold_with_rates)}')
print(f'Rows after outlier removal: {len(sold_clean)}')
print(f'Rows removed: {len(sold_with_rates) - len(sold_clean)}')

print(f'\nMedian ClosePrice before: {sold_with_rates["ClosePrice"].median()}')
print(f'Median ClosePrice after: {sold_clean["ClosePrice"].median()}')

print(f'\nMedian LivingArea before: {sold_with_rates["LivingArea"].median()}')
print(f'Median LivingArea after: {sold_clean["LivingArea"].median()}')

print(f'\nMedian DaysOnMarket before: {sold_with_rates["DaysOnMarket"].median()}')
print(f'Median DaysOnMarket after: {sold_clean["DaysOnMarket"].median()}')


