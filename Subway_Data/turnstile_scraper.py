from datetime import date, timedelta
from bs4 import BeautifulSoup
import urllib
import pandas as pd
from time import sleep

# Define the head of the url we will be crawling through
url_head = 'http://web.mta.info/developers/data/nyct/turnstile/turnstile_'
# Define the column names for the DataFrames we will be working with
cols = ['C/A','UNIT','SCP','DATE1','TIME1','DESC1','ENTRIES1','EXITS1','DATE2',
        'TIME2','DESC2','ENTRIES2','EXITS2','DATE3','TIME3','DESC3','ENTRIES3',
        'EXITS3','DATE4','TIME4','DESC4','ENTRIES4','EXITS4','DATE5','TIME5',
        'DESC5','ENTRIES5','EXITS5','DATE6','TIME6','DESC6','ENTRIES6','EXITS6',
        'DATE7','TIME7','DESC7','ENTRIES7','EXITS7','DATE8','TIME8','DESC8',
        'ENTRIES8','EXITS8']
entry_cols = ['c/a','unit','scp','station','linename','division','date','time','desc','entries','exits']

# Create a blank DataFrame that we will append each week's data to
all_combined = pd.DataFrame(columns=entry_cols)

# This function is a generator that returns all Saturdays in a given year
# as datetime objects
def allsaturdays(year):
    # Create a datetime object for January 1st
    d = date(year, 1, 1)
    # Find the difference between Saturday (5) and Jan 1st's day number
    days_inc = 5 - d.weekday()
    # If the 1st is a Sunday, days_inc will be -1 which causes errors.
    # In this case we set days_inc = 6 which will find us the first Saturday
    if days_inc < 0:
        days_inc = 6
    # Adjust our datetime object to be the first Saturday of the year
    d += timedelta(days = days_inc)
    # Keep returning dates and incrementing until we reach the next year
    while d.year == year:
        yield d
        d += timedelta(days = 7)


# This function takes in date parameters, crawls through the pages for
# each Saturday in our date range, and returns a DataFrame of all turnstile data
# for our date range
# m/d_start is the month and date of the first Saturday in the range we want
# m/d_end is the month and date of the last Saturday in the range we want
def crawl_year(year,m_start,d_start,m_end,d_end):
    # Create a blank DataFrame that we will append each week's data to
    all_combined = pd.DataFrame(columns=entry_cols)
    # Iterate through our list of Saturday's
    for d in allsaturdays(year):
        if d >= date(year,m_start,d_start) and d <= date(year,m_end,d_end):
            sleep(5) # delays for 5 seconds (to prevent overloading the server)
            # Generate the end of the url from the date
            url_tail =  d.strftime('%y') + d.strftime('%m') + d.strftime('%d') + '.txt'
            # Combine the url parts
            url = url_head + url_tail
            # Open the url and create a list of every line on the page
            lines = urllib.urlopen(url).readlines()
            # Write the data to a csv
            with open("turnstileweek.csv", "w") as file_out:
                for line in lines:
                    file_out.write(line+"\n")
            # The csv format was changed on 10/18/2014, we will parse the csv
            # differently depending on this format
            if d < date(2014,10,18):
                # Create a DataFrame from our csv
                df = pd.read_csv('turnstileweek.csv',header=None,names=cols)
                # The csv is formatted such that each line contains 8 data points.
                # We want to split this up so each line in our DataFrame contains one
                # data point.
                # The first 3 columns contain identifying information that we want to
                # include with each data point. We select those columns:
                unit_info = df.iloc[:,0:3]
                # Create an empty DataFrame that we will use to convert our original
                # DataFrame from a wide to long format.
                week_combined = pd.DataFrame(columns=entry_cols)
                # Split up the remaining columns into their 8 data point groups
                for i in range(8):
                    # Each data point group contains 5 columns
                    x = 3 + (5*i)
                    y = 8 + (5*i)
                    # Select the columns
                    entry = df.iloc[:,x:y]
                    # Join this data point with the identifying info in unit_info
                    entry = unit_info.join(entry)
                    # Set our column names so we can concat our DataFrames
                    entry.columns = entry_cols
                    week_combined = pd.concat([week_combined,entry],axis=0)
                    # Some lines in the csv don't have all 8 groups of data, so when
                    # split the blank ones will have NaNs. Drop these rows.
                    week_combined.dropna(axis=0,how='any',inplace=True)
                # Splitting into the 8 groups made our data out of order, so we sort
                # by date and then time
                week_combined.sort_values(by=['date','time'],inplace=True)
                # Concat this weeks DataFrame to our master DataFrame
                all_combined = pd.concat([all_combined,week_combined],axis=0)
            else:
                # Create a DataFrame from our csv
                df = pd.read_csv('turnstileweek.csv',header=0)
                # After 10/18/2014 they fixed the csv to only have one data
                # point per line, so we don't need to split each line into 8
                # groups anymore
                # There are 3 additional columns in this new format which we
                # don't need, so we drop those
                # df.drop(['STATION','LINENAME','DIVISION'],axis=1,inplace=True)
                # Rename the columns (make them lowercase) so they match the
                # column names of our pre 10/18/14 data
                df.columns = entry_cols
                # Concat this weeks DataFrame to our master DataFrame
                all_combined = pd.concat([all_combined,df],axis=0)
            # Print the date so we can keep track of the script's progress
            print d
    # Return the DataFrame containing all the weeks' data for our specified
    # date range
    return all_combined
# Crawl through the pages in the date ranges we need data for
# data2014 = crawl_year(2014,3,29,10,4)
data2015 = crawl_year(2015,1,3,7,4)
data2015
# Save our DataFrames to csv
# data2014.to_csv('turnstile2014.csv')
data2015.to_csv('turnstile2015_stations.csv',ignore_index=True)
