from bs4 import BeautifulSoup
from html_table_parser import parser_functions as parse
import urllib
import pandas as pd
import calendar

# Create a blank DataFrame with 12 columns
# We will concatenate each day's weather reports to this DataFrame
master_df = pd.DataFrame(columns=range(12))

# Scrapes the weather data for a specified date
def get_weather(url, df, date):
    # Open the page and read the html
    html = urllib.urlopen(url).read()
    # Create a Beautiful Soup object of the html
    soup = BeautifulSoup(html, 'html.parser')
    # Find the table html containing the weather data
    table = soup.find('table',{'cellspacing':0, 'cellpadding':0,
                               'id':'obsTable', 'class':'obs-table responsive'})
    # Use html_table_parser to convert this data to a two-dimensional list
    twodim_table = parse.make2d(table)
    # Delete the first list (this is the columns header)
    del twodim_table[0]
    # Convert our two-dimensional list to a DataFrame
    day_df = pd.DataFrame(twodim_table)
    # Some days don't report wind chill, which shifts all the other columns over
    # by one position. If wind chill is reported, we want to drop that column so
    # all dates have uniform columns.
    if len(day_df.columns) == 13:
        day_df.drop(2,axis=1,inplace=True)
        # Reset the column names
        day_df.columns = range(12)
    # Add a column to identify which day this weather data is for
    day_df['date'] = date
    # Concatenate this day's DataFrame to the bottom of the DataFrame that
    # contains all weather data scraped so far
    concat_df = pd.concat([df, day_df], ignore_index=True)
    # Return our concatenated DataFrame
    return concat_df

# Define our url head and tail. We are going to build the middle part of the url
# by iterating through calendar dates below.
url_head = 'https://www.wunderground.com/history/airport/KNYC/'
url_tail = '/DailyHistory.html?req_city=New+York&req_state=NY&req_statename=New+York&reqdb.zip=10001&reqdb.magic=5&reqdb.wmo=99999'

# Create a Calendar object so we can iterate through calendar dates
cal = calendar.Calendar()

# Now we generate the middle part of the url:
# Format is YYYY/MM/DD
# If month or day only has one digit we don't add a preceding 0

# 2014
# We have data for April - September 2014
for month in range(4,10):
    # Iterate through the dates in current month
    for day in cal.itermonthdays(2014, month):
        # This iterator returns some 0's in addition to the month dates, so we
        # want to filter these out.
        if day != 0:
            # Make a string out of the date
            date = '2014/' + str(month) + '/' + str(day)
            # Combine the url parts
            url = url_head + date + url_tail
            # Update our master weather DataFrame using get_weather()
            master_df = get_weather(url, master_df, date)
# 2015
# We have data for January - June 2015
for month in range(1,7):
    # Iterate through the dates in current month
    for day in cal.itermonthdays(2015, month):
        # This iterator returns some 0's in addition to the month dates, so we
        # want to filter these out.
        if day != 0:
            # Make a string out of the date
            date = '2015/' + str(month) + '/' + str(day)
            # Combine the url parts
            url = url_head + date + url_tail
            # Update our master weather DataFrame using get_weather()
            master_df = get_weather(url, master_df, date)

# Drop the columns that we don't need for our analysis
master_df.drop([2,4,5,6,8,11], axis=1, inplace=True)
# Rename the columns
cols = ['time', 'temp', 'humidity', 'wind_speed', 'precip', 'events', 'date']
master_df.columns = cols

# Save to a csv
master_df.to_csv('weather.csv',index=False,encoding='utf-8')
