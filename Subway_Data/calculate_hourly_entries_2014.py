import pandas as pd
import numpy as np
import re
import calendar
from timeit import default_timer as timer
import warnings
warnings.simplefilter('ignore',np.RankWarning)

'''
This script implements an algorithm to distribute the number of entries in each
four hour period into the one hour long periods. We fit a polynomial to the
number of entries a turnstile reports for different times of the week to model
the pattern of entries. This allows us to more accurately distribute the entries
than simply dividing the total entries by 4.
'''

# Read in the data
turn1 = pd.read_csv('./turnstile_2014_save.csv')

# Convert to datetime
turn1.date_time = pd.to_datetime(turn1.date_time,errors='coerce')
turn1.time_since_last = pd.to_timedelta(turn1.time_since_last,errors='coerce')
# Extract the hour of the day
turn1['hour'] = turn1.date_time.apply(lambda t: t.hour)
# Create a new column that is the number of 1 hour periods contained in each
# row of our DataFrame
turn1['hours_since_last'] = turn1.time_since_last.apply(lambda t: t/np.timedelta64(1, 'h'))
turn1['week_hour'] = (turn1.day_num * 24) + turn1.hour

# Initialize a list that will hold the DataFrames we create in the next step.
# We will concat these all at once for efficiency.
df_list = []
# This step very long, initilize a count so we can keep track of how far we are
count = 0

# Now we need to break down each row, which are each for 1 period (3, 4, or 5
# hours long), into 1 hour periods.
for ca in turn1['c/a'].unique():
    temp1 = turn1[turn1['c/a'] == ca]
    # Get the station, linename, and division for this c/a
    station = temp1.station.unique()[0]
    linename = temp1.linename.unique()[0]
    division = temp1.division.unique()[0]
    # Iterate through every unit at this c/a
    for unit in temp1.unit.unique():
        temp2 = temp1[temp1.unit == unit]
        # Iterate through every scp at this unit
        for scp in temp2.scp.unique():
            # Start a timer to make sure there aren't memory problems
            start = timer()
            temp3 = temp2[temp2.scp == scp]
            # Initialize a blank list to store our values
            x = []  # x-axis is hour of the day (military time)
            y = []  # y-axis is average entry_diff for that hour
            # Iterate through every week_hour this turnstile has reports for
            for hour in temp3.week_hour.unique():
                temp4 = temp3[temp3.week_hour == hour]
                # Sometimes there are a small amount of reports for a
                # specific hour. We only want to fit our polynomial on
                # points that have a large number of reports. If there are
                # less than 5 reports we will discard that hour when
                # building our line.
                if len(temp4) > 5:
                    # Get the average entry_diff for this hour
                    hour_avg = temp4.entry_diff.mean()
                    # Append to our lists
                    x.append(hour)
                    y.append(hour_avg)
            # We want to make sure we have enough data points to properly model
            # all 7 days
            if len(x) < 15:
                # If we don't have enough data points, we will do the same step
                # as above, but keep all week_hours regardless of how many
                # reports that week_hour had.
                x = []  # x-axis is hour of the day (military time)
                y = []  # y-axis is average entry_diff for that hour
                for hour in temp3.week_hour.unique():
                    temp4 = temp3[temp3.week_hour == hour]
                    # Get the average entry_diff for this hour
                    hour_avg = temp4.entry_diff.mean()
                    # Append to our lists
                    x.append(hour)
                    y.append(hour_avg)
            # The degree of our polynomial is going to be 1/2 the amount of
            # data points we have
            degree = len(temp3.week_hour.unique())/2
            # Fit a polynomial to our data points
            poly = np.polyfit(x,y,deg=degree)
            # Convert to a 1=dimensional polynomial class
            p = np.poly1d(poly)
            # Iterate through every row for this turnstile
            for index, row in temp3.iterrows():
                # Get the values we will need to determine how many new rows
                # we need to create and for what hours
                num_hours = row.hours_since_last
                d_t = row.date_time
                ent_diff = row.entry_diff
                # Create a blank DataFrame to hold our new rows
                temp_df = pd.DataFrame()
                hour_preds = []
                # We need to create a new row for each hour in this period
                for h in range(int(num_hours)):
                    # Calculate the time for this row
                    new_time = d_t - pd.Timedelta(h,'h')
                    hour_num = new_time.hour
                    day = calendar.weekday(new_time.year,new_time.month,new_time.day)
                    wk_hr = (day*24) + hour_num
                    # Create a dictionary for our new row
                    new_row = {'c/a':ca,'unit':unit,'scp':scp,
                               'station':station,'linename':linename,
                               'division':division,'date_time':new_time,
                               'entry_diff':np.nan,'hour_num':wk_hr}
                    # Convert to a Series
                    new_row = pd.Series(new_row)
                    # Append this row to our DataFrame
                    temp_df = temp_df.append(new_row,ignore_index=True)
                    # Get the expected number of entries for this hour and
                    # append it to our list of expected entries
                    hour_pred = p(wk_hr)
                    # If our polynomial predicts a negative value of entries
                    # for this hour, we want to set the prediction equal to
                    # 0 (there can't be a negative number of entries)
                    if hour_pred < 0:
                        hour_pred = 0
                    hour_preds.append(hour_pred)
                # Sum our expected number of entries for each hour in this
                # period
                periods_sum = sum(hour_preds)
                # Check if periods_sum is 0 (so we don't divide by 0)
                if periods_sum != 0:
                    # Now we need to go through each row that we just created
                    # and fill in the entry_diff
                    for index2, row2 in temp_df.iterrows():
                        # Get the expected entry_diff for this hour
                        hour_pred = p(row2.hour_num)
                        # Change negative values of hour_pred to 0 (can't be
                        # a negative number of entries)
                        if hour_pred < 0:
                            hour_pred = 0
                        # Compute the percent of entry_diff this hour
                        # contributes to the total entry_diff for this period
                        hour_pct = hour_pred/periods_sum
                        # Multiply this percent by the actual number of entries
                        # in this period to calculate our predicted entry_diff
                        hour_diff = hour_pct * ent_diff
                        # Update the entry_diff for this hour's row
                        temp_df.set_value(index2,'entry_diff',hour_diff)
                else:
                    # Since periods_sum is 0, every row will have entry_diff = 0
                    temp_df['entry_diff'] = 0
                # Append the DataFrame we created for this period to our list
                # of temp_dfs
                df_list.append(temp_df)
                end = timer()
            # Print the turnstile information, count, and time to compute this
            # turnstile
            print ca,unit,scp,str(count),str((end - start))
            count += 1

# Concat all the temp_dfs together
turn_hourly = pd.concat(df_list,ignore_index=True)

# Sort our rows so that each individual SCP (for a Unit in a Control Area) is
# sorted in chronological order
turn_hourly = turn_hourly.sort_values(by=['c/a','unit','scp','date_time'])

# Save to a csv
turn_hourly.to_csv('2014_hourly.csv',index=False)
