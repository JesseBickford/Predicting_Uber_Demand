import pandas as pd
import numpy as np
import matplotlib as plt
%matplotlib inline

#Read in the dataset of Uber rides from January 2015 to June 2015 and checkout the first 5 entries
raw2015 = pd.read_csv('/Users/Starshine/DSI/Capstone/uber-raw-data-janjune-15.csv')
raw2015.head()
#We see a locationID and would like to know where each is, so load our other dataset containing locationID and it's location
zones = pd.read_csv('/Users/Starshine/DSI/Capstone/uber-tlc-foil-response/uber-trip-data/taxi-zone-lookup.csv')
zones.head(3)
#Now join the tables on locationID into one comprehensive dataframe. First we have to rename 'locationID' to an uppercase word in our raw2015
raw2015.rename(columns = {'locationID': 'LocationID'}, inplace=True)
#Create a new dataframe set as a merge of our raw2015 and zones, connecting them on LocationID
data = pd.merge(raw2015, zones, on='LocationID')
data.head(25)
#Now it's time to check for our data types and see if we need to convert anything
data.dtypes
#We need to change our 'Pickup_date' to be in datetime format
data['Pickup_date'] = pd.to_datetime(data['Pickup_date'])
data.dtypes
#Now sort our dataframe by chronological date
data = data.sort_values(by='Pickup_date')
data

data.LocationID[('255')].count()
data.hist(layout=(1,2))

#export to a csv for graphing in tableau or merging with other data sets
data.to_csv('2015final.csv')
