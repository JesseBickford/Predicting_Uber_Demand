import pandas as pd
import requests
import json
import calendar
import time

'''
This script uses the weathersource.com API to get weather data for each hour in
our time range. This script replaces weather_scraper.py becuase there was a
large amount of missing hours in that data.
'''

# This function will get hourly weather reports for a specified date
def get_weather(date):
    # Create the timestamp for our time range (one 24-hour period)
    timestamp = ''.join([date,'T00:00,',date,'T24:00'])
    # Define our request parameters
    payload = {'period':'hour','postal_code_eq':'10019','country_eq':'US',
           'timestamp_between':timestamp,'limit':'24',
           'fields':'postal_code,timestamp,temp,precip,precipConf,snowfall,snowfallConf,windSpd,cldCvr,dewPt,feelsLike,relHum,sfcPrec,spcHum,wetBulb'}
    # Make the request and convert to a list of dictionaries
    r = requests.get('https://api.weathersource.com/v1/e06a087bddf03a304b5a/history_by_postal_code.json',
                     params=payload)
    hours = json.loads(r.content)
    # Convert to a DataFrame and return it
    hours_df = pd.DataFrame(hours)
    return hours

# Create a Calendar object so we can iterate through calendar dates
cal = calendar.Calendar()

# This function makes calls to get_weather() for each date in the specified
# date range and returns a DataFrame containing weather data for every hour
def get_weather_range(year,month_start,month_end):
    # Create a blank list to store each dates DataFrame
    hourly_year = []
    # Iterate through the months in our range
    for month in range(month_start,month_end+1):
        # Iterate through the dates in current month
        for day in cal.itermonthdays(year, month):
            # This iterator returns some 0's in addition to the month dates, so
            # we want to filter these out.
            if day != 0:
                # Make a string out of the date
                date = '-'.join([str(year),str(month).zfill(2),
                                 str(day).zfill(2)])
                # Get the weather data for this date and append to the year's
                # list
                hourly_year.append(get_weather(date))
                # Pause for 6 seconds to slow the rate of our requests to the
                # server
                time.sleep(6)

    # Combine each date's DataFrame into a single one for the year
    hourly_year_df = pd.concat(hourly_year)
    # Get rid of any duplicate lines for the same timestamp
    hourly_year_df.drop_duplicates(subset='timestamp',keep='first',inplace=True)
    return hourly_year_df

# Get the weather data for 2014 (April - September)
hourly_2014_df = get_weather_range(2014,4,9)
# There are a few hours that are missing. Weather data for these hours was found
# on a different weather site
temps = [{'cldCvr':0.0,'precip':0.0,'snowfall':0,'spcHum':8.34,'temp':56.4,
          'timestamp':'2014-09-27T05:00:00-04:00','windSpd':1.0},
         {'cldCvr':45.0,'precip':0.0,'snowfall':0,'spcHum':7.60,'temp':69.5,
          'timestamp':'2014-09-22T11:00:00-04:00','windSpd':12.4},
         {'cldCvr':69.0,'precip':0.0,'snowfall':0,'spcHum':7.60,'temp':69.5,
          'timestamp':'2014-09-22T12:00:00-04:00','windSpd':12.4},
         {'cldCvr':0.0,'precip':0.0,'snowfall':0,'spcHum':7.00,'temp':64.0,
          'timestamp':'2014-08-29T01:00:00-04:00','windSpd':3.3}]
# Add the missing hours
hourly_2014_df = hourly_2014_df.append(temps)
# Save to a csv
hourly_2014_df.to_csv('weather_2014.csv',index=False)

# Get the weather data for 2015 (January - June)
hourly_2015_df = get_weather_range(2015,1,6)
# Save to a csv
hourly_2015_df.to_csv('weather_2015.csv',index=False)
