import pandas as pd
import numpy as np
import calendar
import fill_hours

def add_missing_hours(df):
    '''
    This function creates a row for any hour (of a month) that doesn't have a
    ride. For our Tableau visualizations we need at least one entry for each
    hour to ensure the time spacing is consistent. The new rows will have a
    latitude and longitude that is far enough away from the area we are looking
    at that it won't appear on our visualization.
    '''
    # Convert our Date/Time column to datetime
    df['Date/Time'] = pd.to_datetime(df['Date/Time'])
    # Create new columns for the row's day of the month and hour of the day
    df['day'] = df['Date/Time'].apply(lambda t: t.day)
    df['hour'] = df['Date/Time'].apply(lambda t: t.hour)
    # Get the month and year of the data we are looking at.
    # We can assume the DataFrame that is passed to this function only contains
    # data for one month, so we can pull the month and year from any row.
    month = df.ix[0,'Date/Time'].month
    year = df.ix[0,'Date/Time'].year
    # Create a Calendar object
    cal = calendar.Calendar()
    # Iterate through the days of this month
    for day in cal.itermonthdays(year,month):
        # itermonthdays() returns 0s at the start and end, we want to ignore
        # these values.
        if day != 0:
            # Iterate through each hour of the day
            for hour in range(24):
                # Get only the rows that are for this day and hour combination
                day_hour = df[(df.day==day)&(df.hour==hour)]
                # Check to see if there are any rows matching this day and hour
                if len(day_hour) < 1:
                    # If not, we need to create a fake row for this day and hour
                    # Build a string that can be parsed by np.datetime64()
                    date_string = '-'.join([str(year),str(month).zfill(2),str(day).zfill(2)])
                    hour_string = ':'.join([str(hour).zfill(2),'30'])
                    dtime_string = 'T'.join([date_string,hour_string])
                    # Convert our string to datetime
                    dtime = np.datetime64(dtime_string)
                    # Add a new row to the DataFrame. The latitude and longitude
                    # values are far values we picked that are far enough away
                    # from the areas we are going to visualize that they won't
                    # appear on the map. The only column we are updating is
                    # 'Date/Time'.
                    df.loc[len(df)]=['B07777',dtime,'40.728686','-73.84227','1',day,hour]
    # Drop the day and hour columns since they are no longer needed
    df.drop(['day','hour'],axis=1,inplace=True)
    # Return our DataFrame which now contains at least one row for each hour of
    # each day
    return df
