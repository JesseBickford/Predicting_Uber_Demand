import pandas as pd
import fiona
import shapely
import shapely.geometry
import json

'''
This script finds the neighborhood that each ride in our 2014 data set
originates from. To reduce computation time we only find the neighborhood for
each unique latitude/longitude pair.
'''

# Read in the 2014 data
apr = pd.read_csv('/Users/Brian/Downloads/Uber Data/2014/uber-raw-data-apr14.csv')
may = pd.read_csv('/Users/Brian/Downloads/Uber Data/2014/uber-raw-data-may14.csv')
jun = pd.read_csv('/Users/Brian/Downloads/Uber Data/2014/uber-raw-data-jun14.csv')
jul = pd.read_csv('/Users/Brian/Downloads/Uber Data/2014/uber-raw-data-jul14.csv')
aug = pd.read_csv('/Users/Brian/Downloads/Uber Data/2014/uber-raw-data-aug14.csv')
sep = pd.read_csv('/Users/Brian/Downloads/Uber Data/2014/uber-raw-data-sep14.csv')
# Combine the months into one DataFrame
dfs = [apr,may,jun,jul,aug,sep]
combined = pd.concat(dfs)

# Combine the latitude and longitude into one column
combined.Lat = combined.Lat.apply(lambda x: str(x))
combined.Lon = combined.Lon.apply(lambda x: str(x))
combined['lat_lon'] = combined['Lat'] + ' ' + combined['Lon']

# Create a new DataFrame that has only the unique latitude/longitude pairs
combined_unique = pd.DataFrame()
combined_unique['lat_lon'] = combined.lat_lon.unique()
# Re-split the latitude and longitude into two columns
combined_unique['lat'] = combined_unique.lat_lon.apply(lambda x: float(x.split()[0]))
combined_unique['lon'] = combined_unique.lat_lon.apply(lambda x: float(x.split()[1]))

# Open the GeoJSON file which contains our shapes
with open('/Users/Brian/Uber_Project/Subway_Data/neighborhood_shapes.json','r') as f:
    js = json.load(f)

# Create a blank list to store our shapes
shapes = []
# Iterate through each feature and get its shape and NTA id code
for feature in js['features']:
    polygon = shapely.geometry.shape(feature['geometry'])
    nta_id = feature['properties']['NTACode']
    # Append our polygon and nta_id as a tuple
    shapes.append((polygon,nta_id))

# Iterate through the unique_stations
def find_neighborhood(row):
    # Get the longitude and latitude for this station
    # Create a shapely point of this longitude/latitude
    point = shapely.geometry.Point(row.lon,row.lat)
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
                # We found the NTA which contains this point so we can move on
                # to the next point
                return shape[1]

# Find the neighborhood for each unique latitude/longitude pair
combined_unique['nta'] = combined_unique.apply(find_neighborhood,axis=1)
# Merge with the master 2014 DataFrame
combined = combined.merge(combined_unique,on='lat_lon',how='outer')
# Save to csv
combined.to_csv('uber_2014_mapped.csv',index=False)
