# Predicting Uber Demand
This project aims to predict demand for Uber in a New York City neighborhood at a given hour relative to all other neighborhoods. Surge pricing is a reactive solution to a market inefficiency resulting from a mismatch between supply and demand. We want to find a proactive solution and model the relative demand level for each neighborhood in NYC so we can distribute Uber’s fleet in the optimal way. 

###Data Sets
- Uber data from [538’s GitHub repository](https://github.com/fivethirtyeight/uber-tlc-foil-response) which consists of 18.8 million rides in 2014 and 2015.
- Weather data using the [weathersource.com api](https://developer.weathersource.com). Some featues we used are temperature, rain, and humidity.
- Census data from the [2013 American Community Survey](http://maps.nyc.gov/census/). We mined data for both the neighborhood and census track level. Some features we used are distributions of income, age, gender, and number of cars available to each household.
- Subway Turnstile data from the [MTA's website](http://web.mta.info/developers/turnstile.html). There is a relationship between demand for public transportation and demand for Uber, so we wanted to bring in Subway data which can improve our model. This data set consist of the cumulative number of entries and exits reported by each individual turnstile every 4 hours.

### Neighborhood Demand Comparison Animation
One of the first things we did was visualize the differences in how demand varies over time between neighborhoods. Using Tableau, we animated ride pickups hour by hour over a two week period for 4 different neighborhoods. We recorded the animations and synced the videos to have all of them play side-by-side. In the video, a red dot represents a ride that happens in the current hour which will then turn blue and fade away as time passes.

<a href="http://www.youtube.com/watch?feature=player_embedded&v=XEewq1CiFtE
" target="_blank"><img src="http://img.youtube.com/vi/XEewq1CiFtE/0.jpg" 
alt="" width="600" height="450" border="10" /></a>

In Wall Street, we see that demand starts to pick up around noon and stays steady until it quickly declines at midnight. Contrast that with West Village which sees a near constant level of high demand. Times Square is quiet for most of the day except for an increase starting at noon and lasting through the evening rush hour.

This animation helps us visualize that each neighborhood tends to behave differently, so we understand the problem of modeling each neighborhood relative to the others at any time.
