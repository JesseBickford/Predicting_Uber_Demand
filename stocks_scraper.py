from bs4 import BeautifulSoup
import urllib
from html_table_parser import parser_functions as parse
import re
import pandas as pd
import calendar

# Create a blank DataFrame that we will append each month's DataFrame to
cols = ['date','open','high','low','close','volume']
sp = pd.DataFrame(columns=cols)

# Create a Calendar object so we can iterate through calendar dates
cal = calendar.Calendar()

# This function takes in a generated url that contains a month's worth of stock
# data, scrapes it, and then returns a DataFrame of the stock prices
def scrape_stocks(url):
    # Cleans up a string and returns a list of the stock's values for a day
    def sub(s):
        s = re.sub(',','',s)
        s = re.sub('\n',',',s)
        return s.split(',')
    # Read in the html
    html = urllib.urlopen(url).read()
    # Create a BeautifulSoup object for this html
    soup = BeautifulSoup(html, 'html.parser')
    # Select the table which contains the stock data
    table = soup.find('table',{'class':'gf-table historical_price'})
    # Select the second row in this table
    # First row in the data is the headers which we don't need
    # Due to a quirk in the website, every day's stock price is contained
    # in the second row.
    row = table.find('tr').findNext('tr')
    # Convert the row html into a two-dimensional table
    month_tbl = parse.make2d(row)
    # The individual days are separated by '\n\n' in a single string
    # We split based on this to make each day have it's own list index
    month_tbl = month_tbl[0][0].split('\n\n')
    # Remove the commas, then substitute each \n with a comma that we split on
    month_tbl = [sub(day) for day in month_tbl]

    # Create a DataFrame from the month's stock data
    df = pd.DataFrame(month_tbl,columns=cols)
    # The last day of the month is on top, so we reverse the order of the rows
    df = df.reindex(index=df.index[::-1])
    # Return this DataFrame
    return df

# Define the beginning and end portion of the url we will be scraping
url_head = 'https://www.google.com/finance/historical?cid=626307&startdate='
url_tail = '&num=30&ei=SjBHV8nVL5HCjAHpvaWYBg'

# Generate a url for a given year and month
def generate_url(year,month):
    month_days = []
    # Create a list of the days in a month
    for day in cal.itermonthdays(year, month):
        month_days.append(day)
    # Find the last day of the given month (and convert to str)
    last_day = str(max(month_days))
    year = str(year)
    # Convert the month number to a month name
    month = calendar.month_name[month]
    # Construct the middle part of the url
    # Format: 'Apr+1%2C+2014&enddate=Apr+30%2C+2014'
    url_mid = month+'+1%2C+'+year+'&enddate='+month+'+'+last_day+'%2C+'+year
    return url_head + url_mid + url_tail

# Scrape the data for April - September 2014 and append it to our sp DataFrame
for month in range(4,10):
    url = generate_url(2014,month)
    month_df = scrape_stocks(url)
    sp = pd.concat([sp,month_df],ignore_index=True)
# Scrape the data for January - June 2015 and append it to our sp DataFrame
for month in range(1,7):
    url = generate_url(2015,month)
    month_df = scrape_stocks(url)
    sp = pd.concat([sp,month_df],ignore_index=True)

# Save our DataFrame to a csv
sp.to_csv('s_and_p.csv')
