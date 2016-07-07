import pandas as pd

#Read in the weather csv and check its shape
weather = pd.read_csv('/Users/Starshine/DSI/Capstone/weather.csv')
weather.head()

#Join 'date' and 'time' into a single column 'Date'
weather['Date'] = weather[['date', 'time']].apply(lambda x: ' '.join(x), axis=1)
#Convert the new 'Date' column to be in datetime format
weather['Date'] = pd.to_datetime(weather['Date'])
#Drop the redundant columns
weather.drop(['time', 'date'], axis=1, inplace=True)

#Remove the '°F'  and whitespace from the 'temp' column
weather['temp'] = weather.temp.apply(lambda x: x[:-5])

#Remove the '%' from humidity, then rename humidity column
weather['humidity'] = weather.humidity.apply(lambda x: x[:-1])
weather.rename(columns={'humidity':'humidity_pct'}, inplace=True)

#Remove the ' mph' and whitespace from the 'wind_speed' column
weather['wind_speed'] = weather.wind_speed.apply(lambda x: x[:-5])
#replace empty 'wind_speed' cells with a string '0'
weather.wind_speed.replace('', '0', inplace=True)

#Drop the one row with missing 'temp' data
weather.drop(6864, inplace=True)

#export to csv
weather.to_csv('weather_cleaned.csv')
