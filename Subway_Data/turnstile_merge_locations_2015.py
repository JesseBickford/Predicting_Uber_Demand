import pandas as pd
import re

# Read in our csv and convert the date_time columns
hourly_2015 = pd.read_csv('./2015_hourly_combined.csv')
hourly_2015.date_time = pd.to_datetime(hourly_2015.date_time,errors='coerce')

# Sort our rows so that each individual SCP (for a Unit in a Control Area) is
# sorted in chronological order
hourly_2015 = hourly_2015.sort_values(by=['c/a','unit','scp','date_time'])

# Define a function to fix the linenames. Numbers were treated as both strings
# and floats when the csv was read in.
def fix_linename(x):
    if type(x) == float:
        x = int(x)
        return str(x)
    else:
        return str(x)
hourly_2015.linename = hourly_2015.linename.apply(fix_linename)

# There are some stations names that occur more than once in different areas.
# We need to add the linename so we can keep unique stations separated
hourly_2015['station_line'] = hourly_2015['station'] + ' ' + hourly_2015['linename']

# Get the sum of entries at each station at each hour
station_entries = pd.DataFrame({'entries':hourly_2015.groupby(by=['station_line','date_time']).entry_diff.sum()}).reset_index()

# Read in the csv which has station names and their latitude/longitude
stations = pd.read_csv('./subway_stations_nyc_matched.csv')
# Drop the column created by editing the csv
stations.drop('Unnamed: 4',axis=1,inplace=True)

# Format the station name and line and combine in the same format of the
# station_line column in hourly_2015
stations.LINE = stations.LINE.apply(lambda s: re.sub('-','',s))
stations.NAME = stations.NAME.apply(lambda s: s.upper())
stations['station_line'] = stations.NAME + ' ' + stations.LINE

# There are some issues where the same station has multiple station_lines
# Create a dictionary to map the issues to their main station_line
linename_map = {'14 ST-UNION SQ LNQR456':'14 ST-UNION SQ 456LNQR',
                '157 ST 1.0':'157 ST 1',
                '168 ST-BROADWAY AC1':'168 ST-BROADWAY 1AC',
                '34 ST-PENN STA 123ACE':'34 ST-PENN STA 123',
                '42 ST-PA BUS TE ACENGRS1237':'42 ST-PA BUS TE ACENQRS1237',
                '42 ST-TIMES SQ ACENQRS1237':'42 ST-TIMES SQ 1237ACENQRS',
                '59 ST-COLUMBUS ABCD1':'59 ST-COLUMBUS 1ABCD',
                'BARCLAYS CENTER BDNQR2345':'BARCLAYS CENTER 2345BDNQR',
                'BOROUGH HALL/CT R2345':'BOROUGH HALL/CT 2345R',
                'FULTON ST ACJZ2345':'FULTON ST 2345ACJZ',
                'WALL ST 45.0':'WALL ST 45'}
# Map the duplicate station_linenames to their main name
hourly_2015.station_line = hourly_2015.station_line.apply(lambda s: linename_map[s] if s in linename_map.keys() else s)

# Merge our 2 DataFrames on the station_line columns
hourly_2015 = hourly_2015.merge(stations,on='station_line',how='inner')

# Get longitude/latitude from the combined column
hourly_2015['longitude'] = hourly_2015.the_geom.apply(lambda p: p.split()[1][1:])
hourly_2015['latitude'] = hourly_2015.the_geom.apply(lambda p: p.split()[2][:-1])

# Drop the columns we don't need anymore
hourly_2015.drop(['NAME','the_geom','URL','LINE'],axis=1,inplace=True)

# Save to a csv
hourly_2015.to_csv('hourly_2015_locations.csv',index=False)
