import pandas as pd
import numpy as np
import fiona
import shapely
import shapely.geometry
import json

# Open the GeoJSON file which contains our shapes
with open('./neighborhood_shapes.json', 'r') as f:
    js = json.load(f)

# Create a blank list to store our shapes
shapes = []
# Iterate through each feature and get its shape and NTA id code
for feature in js['features']:
    polygon = shapely.geometry.shape(feature['geometry'])
    nta_id = feature['properties']['NTACode']
    # Append our polygon and nta_id as a tuple
    shapes.append((polygon,nta_id))

# Read in our cleaned turnstile data
hourly_2015 = pd.read_csv('./hourly_2015_locations.csv')

# Create a blank DataFrame which will hold the unique stations
stations_unique = pd.DataFrame()
# Get the stations. Each station_line in hourly_2015 will have a single latitude
# and longitude
stations_unique['station_l'] = hourly_2015['station_line'].unique()
# Create columns to store the latitude and longitude for each station
stations_unique['latitude'] = np.nan
stations_unique['longitude'] = np.nan

# Iterate through the unique stations and get their latitude and longitudes
for index, row in stations_unique.iterrows():
    # Get the latitude and longitudes for each station from hourly_2015
    lat = hourly_2015[hourly_2015.station_line==row.station_l].latitude.iloc[0]
    lon = hourly_2015[hourly_2015.station_line==row.station_l].longitude.iloc[0]
    # Update the latitude and longitude values for the station in station_unique
    stations_unique.set_value(index,'latitude',lat)
    stations_unique.set_value(index,'longitude',lon)

# Create a new column which will hold the NTA id code the station is located in
stations_unique['nta_id'] = None

# Iterate through the unique_stations
for index, row in stations_unique.iterrows():
    # Get the longitude and latitude for this station
    lon = row.longitude
    lat = row.latitude
    # Create a shapely point of this longitude/latitude
    point = shapely.geometry.Point(lon,lat)
    # Iterate through our list of shapes
    for shape in shapes:
        # Get the maximum and minimum values for latitude and longitude in this
        # shape
        minx, miny, maxx, maxy = shape[0].bounds
        # Create a box which contains all points in that are within our maximums
        # and minimums
        bounding_box = shapely.geometry.box(minx, miny, maxx, maxy)
        # Check to see if our point if within this box. If not, then the point
        # can't be in the shape and we don't need to check if the point is in
        # shape (which is more computationally expensive)
        if bounding_box.contains(point):
            # If the point is in the box, check if the point is in the shape
            if shape[0].contains(point):
                # Update the nta_id column for this row with the nta_id for this
                # shape
                stations_unique.set_value(index,'nta_id',shape[1])
                # We found the NTA which contains this point so we can move on
                # to the next point
                break

# Drop the latitude and longitude columns from stations_unique because these
# values are already in hourly_2015
stations_unique.drop(['latitude','longitude'],axis=1,inplace=True)
# Merge our DataFrames to add our nta_id column to hourly_2015
hourly_2015 = hourly_2015.merge(stations_unique,how='outer',
                                left_on='station_line',right_on='station_l')
# Drop the station_l column because it is the same as station_line
hourly_2015.drop('station_l',axis=1,inplace=True)

# Save to a csv
hourly_2015.to_csv('hourly_2015_nbhd_locations.csv',index=False)
