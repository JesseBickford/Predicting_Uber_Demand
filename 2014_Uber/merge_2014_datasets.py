import pandas as pd
import re
import numpy as np
import calendar

'''
This script combines our Uber, weather, census, and subway turnstile data into
a single dataset which we will use to build our model.
'''

# Read in the turnstile data
turn = pd.read_csv('./hourly_2014_nbhd_locations.csv')
# Sum the entires grouped by neighborhood and date_time
turn_nbhd = pd.DataFrame({'entries':turn.groupby(by=['nta_id','date_time']).entries.sum()}).reset_index()
# Create a new column that we will use to join on
turn_nbhd['nta_dt'] = turn_nbhd['nta_id'] + ' ' + turn_nbhd['date_time']

# Read in the weather_data
weather = pd.read_csv('./weather_2014.csv')
# Get rid of the UTC offset from the timestamp column
weather.timestamp = weather.timestamp.apply(lambda s: s[:-6])
# Convert to datetime and back to a string for formatting purposes
weather.timestamp = pd.to_datetime(weather.timestamp)
weather.timestamp = weather.timestamp.apply(lambda d: str(d))
# Rename the timestamp column so we can join on date_hour
weather.rename(columns={'timestamp':'date_hour'},inplace=True)
# Drop the columns we aren't going to use in our models
weather.drop(['cldCvr','dewPt','feelsLike','postal_code','spcHum','wetBulb'],
              axis=1,inplace=True)
# Fix a row that has missing values
for col,val in zip(['relHum','temp','windSpd'],[77.5,69,1]):
    weather.set_value(3416,col,val)

# Read in the census data
census = pd.read_csv('./census_final.csv')
# Remove the extra whitespace in some rows neighborhood name
census.nbhd_name = census.nbhd_name.apply(lambda s: s.strip())
# Drop the nta columns (it is redundate with nbhd_id)
census.drop('nta',axis=1,inplace=True)
# Rename the nbhd_id column so we can join on nta
census.rename(columns={'nbhd_id':'nta'},inplace=True)

# Read in the Uber data
uber = pd.read_csv('/Users/Brian/uber_2014_mapped.csv')
# Drop the columns we no longer need
uber.drop(['Lat','Lon','Base','lat_lon'],axis=1,inplace=True)
# This function reformats a string from the Date/Time column into a format that
# we can join on
def get_date_hour(row):
    # Get the datetime for this row
    dt = row['Date/Time']
    # Pull out the year, month, and day
    date = dt.split()[0]
    year = date.split('/')[2]
    month = date.split('/')[0].zfill(2)
    day = date.split('/')[1].zfill(2)
    # Format the date
    date = '-'.join([year,month,day])
    # Get the hour of the day
    hour = dt.split()[1].split(':')[0].zfill(2)
    # Format the time
    time = ':'.join([hour,'00','00'])
    # Join the date and time and return it
    return ' '.join([date,time])
# Create a new column date_hour which we will join on
uber['date_hour'] = uber.apply(get_date_hour,axis=1)

# Sum the Uber rides grouped by neighborhood and date_time
uber_grouped = pd.DataFrame({'rides':uber.groupby(by=['nta','date_hour']).size()}).reset_index()
# Combine the neighborhood id and date_hour into a column that we will join on
uber_grouped['nta_dt'] = uber_grouped['nta'] + ' ' + uber_grouped['date_hour']

# We need to make sure there is a row for each hour in each neighborhood.
# Currently a neighborhood with no rides in an hour doesn't have a row.
# Convert our Date/Time column to datetime
uber_grouped['date_hour'] = pd.to_datetime(uber_grouped['date_hour'])
# Create new columns for the row's day of the month and hour of the day
uber_grouped['month'] = uber_grouped['date_hour'].apply(lambda t: t.month)
uber_grouped['day'] = uber_grouped['date_hour'].apply(lambda t: t.day)
uber_grouped['hour'] = uber_grouped['date_hour'].apply(lambda t: t.hour)
# Create a Calendar object
cal = calendar.Calendar()
# Create a list to hold the new rows we are going to create
new_rows = []
# Iterate through each neighborhood
for nbhd in uber_grouped.nta.unique():
    # Iterate through each month
    for month in uber_grouped.month.unique():
        # Iterate through the days of this month
        for day in cal.itermonthdays(2014,month):
            # itermonthdays() returns 0s at the start and end, we want to ignore
            # these values.
            if day != 0:
                # Iterate through each hour of the day
                for hour in range(24):
                    # Get only the rows that are for this day and hour combination
                    day_hour = uber_grouped[(uber_grouped.nta==nbhd)&(uber_grouped.month==month)&(uber_grouped.day==day)&(uber_grouped.hour==hour)]
                    # Check to see if there are any rows matching this day and hour
                    if len(day_hour) < 1:
                        # If not, we need to create a fake row for this day and hour
                        # Build a string that can be parsed by np.datetime64()
                        date_string = '-'.join([str(2014),str(month).zfill(2),str(day).zfill(2)])
                        hour_string = ':'.join([str(hour).zfill(2),'00','00'])
                        dtime_string = ' '.join([date_string,hour_string])
                        nta_dtime_string = ' '.join([nbhd,dtime_string])
                        # Create a dictionary for this new row and it to the
                        # list of new rows
                        new_row = {'nta':nbhd,'date_hour':dtime_string,
                                   'rides':0,'nta_dt':nta_dtime_string,
                                   'month':month,'day':day,'hour':hour}
                        new_rows.append(new_row)
# Append these new rows to the uber_grouped DataFrame
uber_grouped = uber_grouped.append(new_rows,ignore_index=True)
# Convert the date_hour column to string so we can join on it
uber_grouped.date_hour = uber_grouped.date_hour.apply(lambda d: str(d))

# Merge the Uber data with the turnstile data
combined = uber_grouped.merge(turn_nbhd,on='nta_dt',how='left')
# Replace any NaN entries with 0
combined.entries.fillna(0,inplace=True)
# Drop the duplicate columns from the merge
combined.drop(['nta_id','date_time'],axis=1,inplace=True)

# Merge with the weather data
combined = combined.merge(weather,on='date_hour',how='left')
# Merge with the census data
combined2= combined.merge(census,on='nta',how='left')

# Get rid of any rows for Staten Island. Staten Island would have a separate
# fleet of vehicles than the rest of NYC.
combined = combined[combined.nta.str.contains('SI')==0]
# Drop any neighborhoods with 98 or 99 in thier nta id. These are parks and
# cemetaries and we don't have any census information for these locations.
combined = combined[combined.nta.str.contains('99')==0]
combined = combined[combined.nta.str.contains('QN98')==0]
# Drop the rows with missing humidity data
combined = combined[combined.relHum.notnull()]

# Save our combined DataFrame to a csv
combined.to_csv('2014_combined_final.csv',index=False)
