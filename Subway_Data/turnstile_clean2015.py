import pandas as pd
import numpy as np
from timeit import default_timer as timer
import re
import calendar
import warnings

'''
'station' is the NYC subway station name.
'c/a' is a stairwell or some other type of entrance/exit of the subway which
  has turnstiles. There can be multiple c/a's for a station.
'unit' is a group of turnstiles. There can be multiple units per c/a (i.e. on
  either side of the station attendant).
'scp' is a single turnstile. It records how many people enter and exit and
  reports a cumulative count every 4 hours.
'''

# Read in our csv
turn = pd.read_csv('./turnstile2015_stations.csv')
# Drop the column created from saving to csv before
turn.drop('Unnamed: 0',axis=1,inplace=True)
# Replace / with - in our date column to speed up the conversion to datetime
turn.date = turn.date.apply(lambda x: re.sub('/','-',x))
# Create a new column that combines our date and time columns
turn['date_time'] = turn['date']+' '+turn['time']
# Convert this combined column to datetime
turn.date_time = pd.to_datetime(turn.date_time,errors='coerce')
# Sort our rows so that each individual SCP (for a Unit in a Control Area) is
# sorted in chronological order
turn1 = turn.sort_values(by=['c/a','unit','scp','date_time'])
# We want to remove any rows that aren't a part of the regular every 4-hour
# schedule. The regular entries always occur exactly on the hour. We will create
# new columns for the minutes and seconds of the time they were recorded.
turn1['mins'] = turn1['date_time'].apply(lambda t: t.minute)
turn1['secs'] = turn1['date_time'].apply(lambda t: t.second)
# Filter out the values where the minutes or seconds are not = 00
turn1 = turn1[(turn1.mins == 0) & (turn1.secs == 0)]
# We no longer need these columns so we can delete them
turn1.drop(['mins','secs'],axis=1,inplace=True)

# Reset our index after it got mixed up by our sort
turn1.reset_index(drop=True,inplace=True)

# There is one row that is causing an issue (found much later in this script).
# We will drop it here to fix the problem.
turn1.drop(1963805,axis=0,inplace=True)
turn1.reset_index(drop=True,inplace=True)

# Create a new column for the difference between the cumulative number of
# entries between each row.
# There is an issue where when we switch from one SCP to the next, taking the
# difference of cumulative enrty counts doesn't make sense. Luckily since our
# data set starts on 12/27/14 but we are only looking at data starting on 1/1/15
# we don't have to do anything to correct for this. We can simply drop all rows
# with a date before 1/1/15.
turn1['entry_diff'] = turn1['entries'].diff()

# Sometimes a turnstile reports both a REGULAR and a RECOVER AUD or some other
# 'desc' tpye at the same time. In this case we want to combine them into a
# single row for that time.
# We need to check every turnstile for duplicate times. Start by iterating
# through every c/a
for ca in turn1['c/a'].unique():
    temp1 = turn1[turn1['c/a'] == ca]
    # Iterate through every unit at this c/a
    for unit in temp1.unit.unique():
        temp2 = temp1[temp1.unit == unit]
        # Iterate through every scp at this unit
        for scp in temp2.scp.unique():
            temp3 = temp2[temp2.scp == scp]
            # Get a list of the unique date_times for this turnstile
            uniq_times = temp3.date_time.unique()
            # If every report is for a different time, the length of this
            # turnstiles reports should equal the length of the unique times
            if len(temp3)!= len(uniq_times):
                # If it doesn't, we need to find the times that are duplicated.
                # Go through each date that this turnstile reports for
                for date in temp3.date.unique():
                    temp4 = temp3[temp3['date']==date]
                    # Go through each time on this date
                    for time in temp4.time.unique():
                        temp5 = temp4[temp4['time']==time]
                        # Check if there is more than one entry for this time
                        if len(temp5) > 1:
                            # Get the 'REGULAR' row's index value (same index as
                            # in turn1) <---------
                            reg_ind = temp5[temp5.desc=='REGULAR'].index.values[0]
                            # Get the row index of the other row for this time
                            rec_ind = temp5[temp5.desc!='REGULAR'].index.values[0]
                            # Get the entry_diffs for each row
                            reg_diff = turn1.ix[reg_ind,'entry_diff']
                            rec_diff = turn1.ix[rec_ind,'entry_diff']
                            # If they have different signs, then the one that is
                            # negative is an error and we need to set that value
                            # equal to 0
                            if (reg_diff < 0) and (rec_diff > 0):
                                turn1.set_value(reg_ind,'entry_diff',0)
                            elif (reg_diff > 0) and (rec_diff < 0):
                                turn1.set_value(rec_ind,'entry_diff',0)
                            # If either of these entry_diffs are NaN we need to
                            # set them equal to 0 so the sum doesn't get messed
                            # up
                            if turn1.ix[reg_ind,'entry_diff'] == np.nan:
                                turn1.set_value(reg_ind,'entry_diff',0)
                            if turn1.ix[rec_ind,'entry_diff'] == np.nan:
                                turn1.set_value(rec_ind,'entry_diff',0)
                            # Add the two entry_diffs
                            entry_sum = turn1.ix[reg_ind,'entry_diff'] + turn1.ix[rec_ind,'entry_diff']
                            # Set the entry_diff value for 'REGULAR' row's index
                            turn1.set_value(reg_ind,'entry_diff',entry_sum)
                            # Drop the other row
                            turn1.drop(rec_ind,axis=0,inplace=True)
# Reset our index after we dropped rows
turn1.reset_index(drop=True,inplace=True)

# There is a turnstile where it acts normally until 2/24/15, then it reports a
# very large number of entries and then every entry_diff after that is negative.
# After inspecting the values, it looks like the turnstile is reporting accurate
# entry numbers, but they are being subtracted from the cumulative total instead
# of added. We calculated the mean for each day of the week and reporting time
# combination for the values where the entry_diff was positive and those where
# it was negative. 34 of the negative means were within 1 std dev of the
# positive mean, 7 were within 2 std dev, and only 1 was above 2 standard
# deviations. Based of these values, I believe it is safe to replace the
# negative entry_diffs with their absolute value.
for index, row in turn1[(turn1['c/a']=='A011')&(turn1['unit']=='R080')&(turn1['scp']=='01-00-00')].iterrows():
    turn1.set_value(index,'entry_diff',abs(row.entry_diff))
# There are more turnstiles which have errors like the turnstile above.
# All of these have been checked and decided that they experienced similar
# errors. We will replace all negative entry_diffs in these turnstiles with
# their absolute values also
neg_errors = [['A011','R080','01-00-04'],['A011','R080','01-00-05'],['A025','R023','01-03-02'],
    ['H009','R235','00-06-03'],['J034','R007','00-00-02'],['N063A','R011','00-00-04'],
    ['N063A','R011','00-00-05'],['N063A','R011','00-00-08'],['N111','R284','00-06-01'],
    ['N128','R200','00-00-02'],['N213','R154','00-06-01'],['N305','R017','01-03-04'],
    ['N327','R254','00-06-01'],['N342','R019','01-03-02'],['N508','R453','00-00-02'],
    ['N601','R319','00-00-01'],['R127','R105','00-00-00'],['R148','R033','01-00-01'],
    ['R158','R084','00-06-00'],['R210','R044','00-03-04'],['R227','R131','00-00-00'],
    ['R258','R132','00-00-03'],['R304','R206','00-00-00'],['R310','R053','01-00-02'],
    ['R322','R386','00-00-02'],['R622','R123','00-00-00'],['R646','R110','01-00-01']]
for error in neg_errors:
    ca = error[0]
    unit = error[1]
    scp = error[2]
    for index, row in turn1[(turn1['c/a']==ca)&(turn1['unit']==unit)&(turn1['scp']==scp)].iterrows():
        turn1.set_value(index,'entry_diff',abs(row.entry_diff))
# Same error is happening as the above, except it switches from negative to
# positive. We will replace this turnstile's negative entry_diffs with their
# absolute values.
for index, row in turn1[(turn1['c/a']=='N103')&(turn1['unit']=='R127')&(turn1['scp']=='00-06-00')].iterrows():
    turn1.set_value(index,'entry_diff',abs(row.entry_diff))

# This turnstile only reports 0, -1, -2,or -3 as the entry_diff. Since this
# looks like different type of malfunction and all the entry_diff values are
# low, we will replace all entry_diff with 0
for index, row in turn1[(turn1['c/a']=='A049')&(turn1['unit']=='R088')&(turn1['scp']=='02-05-00')].iterrows():
    turn1.set_value(index,'entry_diff',0)

# There are some rows where it looks like there was an error with the turnstile
# which results in a negative number of entries. We will set then to NaN for now
turn1.ix[((turn1.entry_diff<0)&(turn1.date_time>pd.Timestamp('12-28-2014'))),'entry_diff'] = np.nan

# We want to know how long it has been since each turnstile last reported.
turn1['prev_time'] = turn1['date_time'].shift(1)
# Compare the current time to the previous time
turn1['time_since_last'] = turn1['date_time'] - turn1['prev_time']
# We no longer need the prev_time column so we drop it
turn1.drop('prev_time',axis=1,inplace=True)

# Define a mask so we can find all rows where the SCP is different than the
# SCP of the row before it
mask = turn1.scp != turn1.scp.shift(1)
# Set these columns equal to NaN because their values are not correct
turn1['entry_diff'][mask] = np.nan
# We will assume that each turnstile last reported 4 hours before our data set
# started
turn1['time_since_last'][mask] = np.timedelta64(4,'h')

# We only want the data between 1/1/15 and 6/30/15
turn1 = turn1[(turn1.date_time >= pd.Timestamp('01-01-15')) & (turn1.date_time < pd.Timestamp('07-01-15'))]
# Since we dropped some rows we need to reset the index again
turn1.reset_index(drop=True,inplace=True)

# We need to reset the entry_diff values for when the turnstile reports an
# abnormally large number of entries. However, sometimes a turnstile doesn't
# report for a couple of days so the entry_diff is large but still accurate.
# We will filter out any value where the turnstile reports more than 4000 people
# entered in 8 hours or less.
turn1.ix[((turn1.entry_diff>4000)&(turn1.time_since_last<np.timedelta64(12,'h'))),'entry_diff'] = np.nan
# There are still some large values left (where the time since last report is
# more than 8 hours). We need to see the average number of people entered during
# each 4 hour block of that reporting period.
# First we define a function to see how many 4 hour periods have passed since
# the last report from this turnstile.
def num_periods(time):
    return ((time.days*24)+(time.seconds/3600))/4
# Create a new column of the number of periods since last report
turn1['num_periods'] = turn1['time_since_last'].apply(num_periods)
# Create a new column of the average entries per 4 hours
turn1['avg_ent'] = turn1['entry_diff']/turn1['num_periods']
# Reset the entry_diff where it reports more than 2000 people entering every 4
# hours where the time since last report is greater than 8 hours
turn1.ix[((turn1.avg_ent>2000)&(turn1.time_since_last>pd.Timedelta('08:00:00'))),'entry_diff'] = np.nan
# Drop the avg_ent column because it now has inaccurate values after setting
# some entry_diffs to NaN
turn1.drop('avg_ent',axis=1,inplace=True)

# Create a column that represent the day of the week for each row
# (Monday = 0 through Sunday = 6)
turn1['day_num'] = turn1['date_time'].apply(lambda t: calendar.weekday(t.year,t.month,t.day))

# Create a column to let us know if the entry_diff for each row is original or
# if it has been predicted from other rows. We will set every row to 0, and when
# we change a row's entry_diff we will set imputed = 1
turn1['imputed'] = 0

# For values that were reset to NaN, we need to get a predicted value to replace
# the NaN with.
for index in turn1[(turn1.entry_diff.isnull())&(turn1.num_periods==1)].index.values:
    ca = turn1.ix[index,'c/a']
    unit = turn1.ix[index,'unit']
    scp = turn1.ix[index,'scp']
    day = turn1.ix[index,'day_num']
    time = turn1.ix[index,'time']
    # First we check if there is only one entry for this turnstile
    this_turnstile = turn1[(turn1['c/a']==ca)&(turn1['unit']==unit)&(turn1['scp']==scp)]
    if len(this_turnstile) == 1:
        # If there is only one row for this turnstile we will drop it because
        # there is no useful data for this turnstile.
        turn1.drop(index,axis=0,inplace=True)
    # Check to see if there are any entries for this turnstile where entry_diff
    # is greater than 0
    elif this_turnstile.entry_diff.sum() == 0:
        # If they are all 0 we set this entry_diff = 0 also
        turn1.set_value(index,'entry_diff',0)
        turn1.set_value(index,'imputed',1)
    # Else we potentially have useful data to predict from
    else:
        # Find all rows where this specific turnstile reported on the same day
        # of the week and at the same time. We also get rid of any rows that are
        # NaN or are for longer than one 4 hour period.
        similar = turn1[(turn1['c/a']==ca)&(turn1['unit']==unit)&(turn1['scp']==scp)&(turn1['day_num']==day)&(turn1['time']==time)&(turn1['entry_diff'].notnull())&(turn1.num_periods==1)]
        # Calculate the average entry_diff for this turnstile at this time on
        # this day of the week
        sim_avg= similar.entry_diff.mean()
        # Check to see how many similar entries there are
        if len(similar) < 5:
            # If it is less than 5 we want to look at more data.
            # We will look at all turnstiles in the same unit instead of just
            # this specific turnstile
            similar2 = turn1[(turn1['c/a']==ca)&(turn1['unit']==unit)&(turn1['day_num']==day)&(turn1['time']==time)&(turn1['entry_diff'].notnull())&(turn1.num_periods==1)]
            if len(similar2) < 5:
                # If this is still less than 5, we don't have enough data for
                # our prediction to be reliable. We will set entry_diff = 0
                turn1.set_value(index,'entry_diff',0)
                turn1.set_value(index,'imputed',1)
            else:
                # Else we can use this unit's data to predict
                sim2_avg= similar2.entry_diff.mean()
                # There is either correct entry_diffs in the rows or they are
                # all NaN
                if np.isnan(sim2_avg):
                    # If this average is NaN we will set the entry_diff = 0
                    turn1.set_value(index,'entry_diff',0)
                    turn1.set_value(index,'imputed',1)
                else:
                    # Replace our NaN with the average value we calulcated
                    turn1.set_value(index,'entry_diff',sim2_avg)
                    turn1.set_value(index,'imputed',1)
        # Else we can use this turnstile's similar data to predict
        else:
            # There is either correct entry_diffs in the rows or they are
            # all NaN
            if np.isnan(sim_avg):
                # If so, we will set the entry_diff = 0
                print ca,unit,scp,day,time
                turn1.set_value(index,'entry_diff',0)
                turn1.set_value(index,'imputed',1)
            else:
                # Replace our NaN with the average value we calulcated
                turn1.set_value(index,'entry_diff',sim_avg)
                turn1.set_value(index,'imputed',1)
# Since we dropped some rows we need to reset the index again
turn1.reset_index(drop=True,inplace=True)

# There are some rows that are for more than 14 days worth of 4 hour periods but
# have an entry_diff of less than 50. The max entry_diff per 1 hour period these
# rows could have is .42 people. Since these rows are very computationally
# expensive and have such small entry_diff values (and are potentially system
# errors) we will set their entry_diff = 0
turn1.ix[((turn1.num_periods>1)&(turn1.entry_diff.notnull())&(turn1.time_since_last>pd.Timedelta('14 days'))&(turn1.entry_diff<50)),'entry_diff'] = 0

# We are only interested in data for the subway lines, so we will get rid of all
# turnstiles for PATH train, Roosevelt Island Tram, Staten Island Railway, and
# the LIRR (which are also included in our data set).
turn1 = turn1[(turn1.division!='RIT')&(turn1.division!='LIB')&(turn1.division!='PTH')&(turn1.division!='SRT')]
# Since we dropped some rows we need to reset the index again
turn1.reset_index(drop=True,inplace=True)

# For the values that are still null (reports for multiple periods where the
# entry_diff value was extremely large), set them equal to 0
turn1.ix[turn1.entry_diff.isnull(),'entry_diff'] = 0

# Create empty lists that we will use in the next step
null_list = []
to_drop = []

# For rows that cover more than 1 periods, we need to break them down into
# multiple 4 hour periods. We will calculate the average entry_diff for each 4
# hour period contained in this row, and use that distribution to calculate
# expected entry_diff for each individual period.
for index in turn1[(turn1.num_periods>1)&(turn1.entry_diff.notnull())].index.values:
    print index
    # Get the values we will need to create new rows for each 4 hour period
    ca = turn1.ix[index,'c/a']
    unit = turn1.ix[index,'unit']
    scp = turn1.ix[index,'scp']
    station = turn1.ix[index,'station']
    linename = turn1.ix[index,'linename']
    division = turn1.ix[index,'division']
    day = turn1.ix[index,'day_num']
    time = turn1.ix[index,'time']
    periods = turn1.ix[index,'num_periods']
    # Get the previous entry's information so we know which date & time to
    # start at
    prev_day = turn1.ix[index-1,'day_num']
    prev_time = turn1.ix[index-1,'time']
    prev_date_time = turn1.ix[index-1,'date_time']
    # Initialize the variables we will increment below
    next_time = int(prev_time[:2])
    next_day = prev_day
    next_date_time = prev_date_time
    times = []
    # Calculate the date_time for each new 4 hour period we are creating
    for i in range(int(periods)):
        this_time = []
        # Increment the hours by 4
        next_time += 4
        # Check if time is 24 hours or greater, in which case update the day too
        if next_time > 23:
            # Keep next_time in the range of 0-23 hours
            next_time = next_time % 24
            # Increment the day_num
            next_day += 1
            # CHeck if day is 7 days
            if next_day > 6:
                # Keep day_num in the range of 0-6
                next_day = next_day % 7
        # Increment the date_time
        next_date_time += pd.Timedelta('4 hours')
        # Append this periods values to a list
        this_time.append(next_day)
        this_time.append(next_time)
        this_time.append(next_date_time)
        # Append this period's list to the list of all periods
        times.append(this_time)
    # Create a blank DataFrame for 4 hour periods we are going to create
    temp_df = pd.DataFrame()
    # Go through each of our time's we need to create a period for
    for new_time in times:
        # Unpack this period's values
        day = new_time[0]
        time = new_time[1]
        d_time = new_time[2]
        # Format the date and time variables
        date = '-'.join([str(d_time.month).zfill(2), str(d_time.day).zfill(2), str(d_time.year)])
        time = ':'.join([str(time).zfill(2),'00','00'])
        # Create a dictionary for this new row
        new_row = {'c/a':ca,'unit':unit,'scp':scp,'station':station,
                   'linename':linename,'division':division,'date':date,
                   'time':time,'desc':'IMPUTED','entries':np.nan,
                   'exits':np.nan,'date_time':d_time,'entry_diff':np.nan,
                   'time_since_last':pd.Timedelta('4 hours'),
                   'num_periods':1,'day_num':day,'imputed':1}
        # Convert to a Series
        new_row = pd.Series(new_row)
        # Append this Series to the DataFrame
        temp_df = temp_df.append(new_row,ignore_index=True)
    # Get the total number of entries since the last report
    total_entries = turn1.ix[index,'entry_diff']
    # If total_entries is 0, each time period in between will have entries = 0
    # and we don't need to do any calculations
    if total_entries == 0:
        temp_df['entry_diff'] = 0
    else:
        # Create a blank list to hold our average entry_diffs. This list will
        # be in order from the first 4 hour period we create to the last
        averages = []
        # Check to see if our time period is longer than 1 week. If so, we will
        # make a change to our algorithm to speed up the computation.
        if int(periods) <= 42:
            # Iterate through each of the new rows we created above
            for temp_index, temp_row in temp_df.iterrows():
                # Get the date and time for this row
                day = temp_row.day_num
                time = temp_row.time
                # Find the entries for this turnstile on the same day_num and
                # time. Only get non-null values that are for 1 period and
                # aren't imputed
                similar = turn1[(turn1['c/a']==ca)&(turn1['unit']==unit)&(turn1['scp']==scp)&(turn1['day_num']==day)&(turn1['time']==time)&(turn1['entry_diff'].notnull())&(turn1.num_periods==1)&(turn1.imputed==0)]
                # Calculate the mean entry_diff of the similar values
                similar_avg = similar.entry_diff.mean()
                # Append this mean to our list of averages
                averages.append(similar_avg)
        else:
            # If we have more than 42 periods that means our time period is
            # longer than 1 week. The similar_avg will be the same for each
            # specific day_num and time combination. We only have to calculate
            # each one of these once, and then as we iterate through the new
            # rows we created above pull the similar_avg for that rows day_num
            # and time.
            # Create a dictionary to hold our similar_avg for each combination
            day_time_dict = {}
            # Iterate through each day_num and time combination
            for day in range(0,7):
                for time in temp_df.time.unique():
                    # Create a string for this day and time combination which
                    # will be our dictionary key
                    day_time_ident = str(day) + ' ' + time
                    # Find the entries for this turnstile on the same day_num
                    # and time. Only get non-null values that are for 1 period
                    # and aren't imputed
                    similar = turn1[(turn1['c/a']==ca)&(turn1['unit']==unit)&(turn1['scp']==scp)&(turn1['day_num']==day)&(turn1['time']==time)&(turn1['entry_diff'].notnull())&(turn1.num_periods==1)&(turn1.imputed==0)]
                    # Calculate the mean entry_diff of the similar values
                    similar_avg = similar.entry_diff.mean()
                    day_time_dict[day_time_ident] = similar_avg
            # Iterate through each of the new rows we created above
            for temp_index, temp_row in temp_df.iterrows():
                # Get the date and time for this row
                day = int(temp_row.day_num)
                time = temp_row.time
                # Create the identifying string to access the dictionary
                day_time_ident = str(day) + ' ' + time
                # Append this day_num and time's similar_avg to the list
                # of averages (which are in ascending chronological order)
                averages.append(day_time_dict[day_time_ident])
        # Calculate the sum of the averages
        averages_total = sum(averages)
        #### TEMP CHECK #####
        if np.isnan(averages_total):
            null_list.append(index)
        # Check to make sure our total isn't 0 (so we don't try to divide by 0)
        if averages_total == 0:
            # If it is, set the prediction for every period = 0
            predicted_entries = [0 for average in averages]
        else:
            # Calculate the percent each period contributes to the total average
            # entry_diff over the total time period
            percentages = [average/averages_total for average in averages]
            # Multiply each percent by the total entries over the time period
            # to calculate the estimated entry_diff for each 4 hour period
            predicted_entries = [percent*total_entries for percent in percentages]
        # Update the entry_diff column of our new rows DataFrame to equal their
        # predicted entry_diff
        temp_df['entry_diff'] = predicted_entries
    # Append this DataFrame of new rows to our main DataFrame
    turn1 = turn1.append(temp_df,ignore_index=True)
    # Add the index of the row that was for multiple periods to a list
    # We will drop all of these values after completing this for loop so we
    # don't mess up the index values
    to_drop.append(index)

# 'Save point'
# turn1.to_csv('turnstile2015_clean_temp2.csv',index=False)
# turn1 = pd.read_csv('turnstile2015_clean_temp2.csv',low_memory=True)
# turn1.date_time = pd.to_datetime(turn1.date_time,errors='coerce')
# turn1.time_since_last = pd.to_timedelta(turn1.time_since_last,errors='coerce')

# Get rid of all rows for more than 1 period
turn1 = turn1[turn1.num_periods <= 1]

# Drop the rows that we split into 4 hour period rows
turn1.drop(turn1.index[to_drop],axis=0,inplace=True)
# Since we dropped some rows we need to reset the index again
turn1.reset_index(drop=True,inplace=True)
# Re-sort our rows so that each individual SCP (for a Unit in a Control Area) is
# sorted in chronological order
turn1 = turn1.sort_values(by=['c/a','unit','scp','date_time'])

# Create a new column that is an integer representation of the hour of the day
# for each report (in military time)
turn1['hour'] = turn1.date_time.apply(lambda t: t.hour)
# Create a new column that is the number of 1 hour periods contained in each
# row of our DataFrame
turn1['hours_since_last'] = turn1.time_since_last.apply(lambda t: t/np.timedelta64(1, 'h'))

# We are going to fit a polynomial to a weeks worth of data. Create a new column
# that represents the hour of the week (0 is Monday at 12am)
turn1['week_hour'] = (turn1.day_num * 24) + turn1.hour

# Get a count of the unique turnstiles in our dataset
count = 0
for ca in turn1['c/a'].unique():
    temp1 = turn1[turn1['c/a'] == ca]
    for unit in temp1.unit.unique():
        temp2 = temp1[temp1.unit == unit]
        for scp in temp2.scp.unique():
            count += 1
print 'Number of unique turnstiles:', count

# Initialize a list that will hold the DataFrames we create in the next step.
# We will concat these all at once for efficiency.
df_list = []
# This step very long, initilize a count so we can keep track of how far we are
count = 0
# Supress RankWarnings that occur when fitting polynomials
warnings.simplefilter('ignore',np.RankWarning)

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

# Concat the all the temp_dfs together
turn_hourly = pd.concat(df_list,ignore_index=True)

# Sort our rows so that each individual SCP (for a Unit in a Control Area) is
# sorted in chronological order
turn_hourly = turn_hourly.sort_values(by=['c/a','unit','scp','date_time'])

# Save to a csv
turn_hourly.to_csv('2015_hourly_combined.csv',index=False)

'''
# Checking to see how many turnstiles don't have data starting on 12/27/14
for ca in turn1['c/a'].unique():
    temp1 = turn1[turn1['c/a'] == ca]
    for unit in temp1.unit.unique():
        temp2 = temp1[temp1.unit == unit]
        for scp in temp2.scp.unique():
            temp3 = temp2[temp2.scp == scp]
            temp4 = temp3[temp3.date == '12-27-2014']
            if len(temp4)<1:
                print ca,unit,scp
                temp5 = turn1[(turn1['c/a']==ca)&(turn1['unit']==unit)&(turn1['scp']==scp)]
                ent = temp5.iloc[0].entries
                ext = temp5.iloc[0].exits
                dt = temp5.iloc[0].date
                print dt
                print ent, ext
'''

'''
# Test to make sure there are no more turnstiles with more than one entry_sum
# for a specific date_time
for ca in turn1['c/a'].unique():
    temp1 = turn1[turn1['c/a'] == ca]
    for unit in temp1.unit.unique():
        temp2 = temp1[temp1.unit == unit]
        for scp in temp2.scp.unique():
            temp3 = temp2[temp2.scp == scp]
            uniq_times = temp3.date_time.unique()
            if len(temp3)!= len(uniq_times):
                for date in temp3.date.unique():
                    temp4 = temp3[temp3['date']==date]
                    for time in temp4.time.unique():
                        temp5 = temp4[temp4['time']==time]
                        if len(temp5) > 1:
                            print ca,unit,scp,date,time
'''
