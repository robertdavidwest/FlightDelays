# FlightDelays

I set out to take data on obsereved historical flights and create a model that successfully predicts flight delays, using Python's Sci-Kit library. To create a predictive model and to understand the contributing factors to the model.

* To see the more detailed analysis see [here](https://github.com/robertdavidwest/airports/blob/master/airports/analysis/run_model.ipynb)
* and for all code used to obtain, aggregate and clean data see [here](https://github.com/robertdavidwest/airports)

## Data Sources

The final dataset used to train the model was comprised of three different data sources:

1. Flight level data from the [Bureal of Transportation Statistics](http://www.transtats.bts.gov/DL_SelectFields.asp?Table_ID=236&DB_Short_Name=On-Time)
2. Daily Weather information at both the origin and destination airport [ncdc.noaa.gov](http://www.ncdc.noaa.gov/cdo-web/datasets/)
3. Aircraft specific information from [registry.faa.gov](http://registry.faa.gov/aircraftinquiry/NNum_Results.aspx?NNumbertxt=N325US)
 
## The Model

* The model was trained and tested using data from 2013 flights to predict flight delays in 2014
* A flight delay was defined as any flight that took off more than 15 minutes after its scheduled departure time
* The final model used to predict flight delays was a RandomForestClassifier trained on data from all 3 file sources.

## Summary

* I used a single airport (JFK) to train the model and find the best fit. I then applied this methodology to the top 5 busiest airports in the united states by total passengers boarding:
	* Atlanta (ATL)
	* Los Angeles (LAX)
	* O'Hare - Chicago (ORD)
	* Dallas/Fort Worth (DFW)
	* John F. Kennedy - New York (JFK)
 
	to observe model performance and whether factor siginificance would differ by airport

* Across the 5 airports the distribution of flight delays is similar (data from 2013):

		                 ATL            LAX            ORD            DFW           JFK
		OnTime Flights   0.811248       0.807899       0.718161       0.767909      0.813833
		Delayed Flights  0.188752       0.192101       0.281839       0.232091      0.186167
		Total  			 267,647 		 170,796        208,818        211,232       83,742

Using 2013 data to train this model, the following represents the model's performance on the 2014 data:
	
* The model performed similarly across the 5 airports with the best predictive power seen at JFK
* Across all 5 airports the two most significant factors contributing to flight delays were 'Hour' the Hour in the day and 'AirTime' the total flight time. Both of which had a negative correlation with Delays. i.e. the later in the day you're flight is scheduled to leave and the longer your flight, the more likely a delay

		show correlation matrix for JFK data of these two factors
		show JFK hour histogram and AirTime

	NOTE: the hours between midnight and 3am were recoded as 24 to 27 respectively. 
	
* CHECK LOCATION OF ORIGIN WEATHERS VARS TO SEE IF THEY DIFFER BY AIRPORT
* For all aiports but Atlanta, the third most significant factor was the temperature (daily high) at the destination airport. Interestingly Atlanta sees a boost in significance of the year of Manufacteur of the aircraft
	
	show year of manufacteura distribution across airports


## Model Results

	
	MODEL PERFORMANCE METRICS
	-------------------------
	
	                ATL       LAX       ORD       DFW       JFK
	Precision  0.528227  0.612642  0.572036  0.609801  0.582480
	Recall     0.142244  0.122005  0.226480  0.177175  0.244387
	F1         0.224132  0.203487  0.324488  0.274574  0.344313
	Accuracy   0.814117  0.816518  0.734237  0.782718  0.826718
	
	
	FACTOR SIGINIFICANCE - TOP 5 FACTORS 
	------------------------------------
	              ATL		       LAX		        ORD             DFW             JFK
	   Feature  Score  Feature   Score   Feature  Score   Feature  Score Feature   Score
	1. Hour     0.17   Hour       0.18   Hour      0.17   Hour     0.18  Hour       0.21
	2. AirTime  0.11   AirTime    0.14   AirTime   0.13   AirTime  0.15  AirTime    0.11
	3. MFR Year 0.07   DestTMAX   0.07   DestTMAX  0.07   DestTMAX 0.08  DestTMAX   0.06
	4. DestTMIN 0.07   DestTMIN   0.07   DestTMIN  0.07   DestTMIN 0.08  DestTMIN   0.06
	5. DestTMAX 0.07   DayofMonth 0.07   Dest      0.06   Dest     0.07  OriginTMIN 0.05
	
## Details

* To see more detail on model selection see the [ipython notebook](https://github.com/robertdavidwest/airports/blob/master/airports/analysis/run_model.ipynb)
* To see full details on the intermediate data gathering and manipulation work, see the github repo: [https://github.com/robertdavidwest/airports](https://github.com/robertdavidwest/airports)