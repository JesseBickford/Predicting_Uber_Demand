import requests
import json
import pandas as pd
import time
import math
import random

def get_areas(url,payload):
    """
    Gets a list of all census tracts or neighborhoods in NYC
    Returns a DataFrame that also includes the burough and id code for the area
    """
    # Define the request headers and payload
    headers = {'Accept':'*/*',
            'Accept-Encoding':'gzip, deflate, sdch',
            'Accept-Language':'en-US,en;q=0.8',
            'Cache-Control':'max-age=0',
            'Connection':'keep-alive',
            'Content-Type':'application/x-www-form-urlencoded',
            'Cookie':'JSESSIONID=DF1B195C91D3F94E1D5FC65EA4A63031; WT_FPC=id=217344d542160f164a81466367471337:lv=1466373814829:ss=1466372100422; msplva-gisappvip.appdmz.nycnet_80_COOKIE=R3993650177',
            'Host':'maps.nyc.gov',
            'Referer':'http://maps.nyc.gov/census/',
            'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
            'X-Requested-With':'XMLHttpRequest'}
    # Create a request and send it to the server with our specified arguments
    s = requests.Session()
    content = s.post(url,headers=headers,data=payload)
    response_string = content.content
    # Remove the first four characters of the content (they are '{}&&')
    response_string = response_string[4:]
    # Convert from string to dictionary
    locations = json.loads(response_string)
    # Make a DataFrame of the neighborhoods/census tracts
    locations_df = pd.DataFrame(locations['items'])
    # Return the DataFrame
    return locations_df

def profileRequest(area_type,tract_id):
    if area_type == 'tract':
        return '{"ids":"' + tract_id + '","featureType":"CENSUS_TRACT"}'
    elif area_type == 'neighborhood':
        return '{"ids":"' + tract_id + '","featureType":"V_DCP_NEIGHBORHOOD"}'

def get_data(request_url,tract_id,area_type):
    # Put the tract_id into the profileRequest string and define our payload
    profile_req = profileRequest(area_type,tract_id)
    payload = {'_v':'"15.0.0.5"',
               'profileRequest':profile_req}
    # Create a request and send it to the server with our specified arguments
    s = requests.Session()
    content = s.post(request_url, data=payload)
    # Get the data from the response
    data_string = content.content
    # Convert from string to dictionary
    data = json.loads(data_string)
    # Convert to series and name the series as the tract_id
    data = pd.Series(data)
    data.rename(tract_id,inplace=True)
    # Return the Series
    return data

def get_input():
    # Let the user know the question we are asking
    print 'Do you want neighborhood or census tract data?'
    while True:
        # Ask the user to enter one of the specified responses
        answer = raw_input("  Enter 'neighborhood' or 'tract': ")
        # Check to see if they entered a valid response
        if answer.lower() == 'neighborhood' or answer.lower() == 'tract':
            # If it was valid, return their response
            return answer.lower()

def random_time():
    # Generate a random float number (x) between 0 and 2, and return e^x
    return math.exp(random.uniform(0,2))

# Define the URL and payload for obtaining a list of all census tracts
tracts_url = 'http://maps.nyc.gov/doitt/webmap/AreaLookup?featureTypeName=CENSUS_TRACT&filterAttrs=BOROUGH&dojo.preventCache=1466377485066'
tracts_payload = {'featureTypeName':'CENSUS_TRACT',
            'filterAttrs':'BOROUGH',
            'dojo.preventCache':'1466377485066'}
# Define the URL and payload for obtaining a list of all neighborhoods
neighborhood_url = 'http://maps.nyc.gov/doitt/webmap/AreaLookup?featureTypeName=V_DCP_NEIGHBORHOOD&filterAttrs=BOROCODE&dojo.preventCache=1466454561146'
neighborhood_payload = {'featureTypeName':'V_DCP_NEIGHBORHOOD',
           'filterAttrs':'BOROCODE',
           'dojo.preventCache':'1466454561146'}

# Define the URLs for requesting specific types of census data
demographics_url = 'http://maps.nyc.gov/census/data/getAcsDemoData'
social_url = 'http://maps.nyc.gov/census/data/getAcsSocialData'
economic_url = 'http://maps.nyc.gov/census/data/getAcsEconomicData'
housing_url = 'http://maps.nyc.gov/census/data/getAcsHousingData'

def crawl_locations(area_type):
    # Create blank DataFrames for each type of census data
    demo_df = pd.DataFrame()
    social_df = pd.DataFrame()
    economic_df = pd.DataFrame()
    housing_df = pd.DataFrame()
    # Check if we are getting data for census tracts or neighborhoods
    if area_type == 'tract':
        # Get the list of census tracts
        areas = get_areas(tracts_url, tracts_payload)
        # Define the identifying string we will append to the filename
        area_string = 'tract'
    elif area_type == 'neighborhood':
        # Get the list of neighborhoods
        areas = get_areas(neighborhood_url, neighborhood_payload)
        # Define the identifying string we will append to the filename
        area_string = 'nbhd'
    # Get the census data for each individual census tract/neighborhood
    for area in areas.name.values:
        if area != '5008900':
            print area
            # Get this area's demographic data
            demographics = get_data(demographics_url,area,area_type)
            demo_df = demo_df.append(demographics)
            # Get this area's social data
            social = get_data(social_url,area,area_type)
            social_df = social_df.append(social)
            # Get this area's economic data
            economic = get_data(economic_url,area,area_type)
            economic_df = economic_df.append(economic)
            # Get this area's housing data
            housing = get_data(housing_url,area,area_type)
            housing_df = housing_df.append(housing)
            # Sleep for a random length of time after each area to prevent
            # overloading the server with requests
            #time.sleep(random_time())
            t = random_time()
            print t
            time.sleep(3+t)
    # Save each DataFrame to csv
    # (Append an identifier to the front of each filename to differentiate
    # between census tract/neighborhood csv)
    demo_df.to_csv(area_string+'_demographics.csv')
    social_df.to_csv(area_string+'_social.csv')
    economic_df.to_csv(area_string+'_economics.csv')
    housing_df.to_csv(area_string+'_housing.csv')

# Ask the user what geographic level they want information for
area_type = get_input()
# Get the data for that geographic level
crawl_locations(area_type)
