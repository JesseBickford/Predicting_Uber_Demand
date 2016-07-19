import pandas as pd
import numpy as np
import calendar

'''
This script computes the classification group for each row in our data set.
We are classifying number of rides into n quantile groups representing levels of
demand for a neighborhood compared to every other neighborhood at that hour.
We compute the quantiles for each hour and determine which quantile each row is
in.
'''

# Read in the combined data set
data = pd.read_csv('./2014_combined_final.csv')

# We are only going to look at the neighborhoods in Manhattan
data = data[data.nta.str.contains('MN')]

# This function computes the values which separate each quantile. n is the
# number of quantiles
def compute_quantiles(df,n):
    # Compute the fraction each quantile will represent
    x = float(100)/n
    # Compute the percent that each quantile is separated at
    quantiles = [x*i for i in range(1,n)]
    # Return the number of rides that separates each quantile
    return np.percentile(df.rides,quantiles)

def get_quantiles(n):
    # Create a list to hold the quantiles for each date_hour
    quantiles_list = []
    # Iterate through each date_hour in our data set
    for date_hour in data.date_hour.unique():
        # Get the neighborhood rows for this date_hour
        dh = data[data.date_hour == date_hour]
        # Compute the quantile values for this date_hour and number of quantiles
        quantiles = pd.Series(compute_quantiles(dh,n))
        # Name the series as the date_hour so this will be our index
        quantiles.rename(date_hour,inplace=True)
        # Add this date_hour's quantile values to the list
        quantiles_list.append(quantiles)
    # Create a DataFrame of each date_hour quantile values
    quantiles_df = pd.DataFrame(quantiles_list)

# We are going to classify into n=3 groups
quantiles_df = get_quantiles(3)

# This function calculates the classification group for each row
def ride_group(row):
    # Get the date_hour and number of rides for this row
    dh = row.date_hour
    rides = row.rides
    # Get the quantile values for this date_hour
    dh_quantiles = quantiles_df.ix[dh]
    # Initialize a count value which represent the classification group we are
    # checking
    count = 0
    # Iterate through each
    for val in df_quantities:
        # Check if this row's rides is below this cut-off value
        if rides < val:
            return count
        else:
            # If it isn't, we increment count and check the next cut-off value
            count += 1
    # If the number of rides is higher than each cut-off value then this row
    # belongs in the final classification group
    return count

# Calculate the classification group for each row
data['classification'] = data.apply(ride_group,axis=1)

# Convert the date_hour columns to datetime
data.date_hour = pd.to_datetime(data.date_hour)
# Intialize a Calendar object
cal = calendar.Calendar()
# Determine the day of the week for each row (we will use this in our model)
data['week_day'] = data.date_hour.dt.weekday

# Save to a csv
data.to_csv('2014_manhattan_classified.csv',index=False)
