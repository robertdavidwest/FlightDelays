## Airports

An [sklearn](http://scikit-learn.org/stable/) model used to predict Flight Delays using data obtained from 3 different sources:

* Flight Data: **ADD FLIGHT DATA SITE HERE**
* Weather Data **ADD FLIGHT DATA SITE HERE**
* Aircraft data **ADD FLIGHT DATA SITE HERE**

This module will instruct you on how to obtain, and combine all of the data above and then describe the process of predicting Flight Delays using a [RandomForestClassifier](http://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html)

## Dependencies 

* Install packages `sklearn`, `matplotlib`, `pandas`, `numpy` and `geopy` using:

		$ pip install <package_name>

* Install package `flyingpandas` by cloning and following installation instructions from [here](https://github.com/robertdavidwest/flyingpandas)

## Get Data Instructions

NOTE: The following steps could easily be simplified to a single run file once the process is final.
The model assumes you already have the two data files `airports new.xlt` and `carriers.xls` saved in `output_dir`.

1. In the file `airport.config.py` enter the variables `output_dir` (the directory used to store all data) and `hdf_path` (the name of the HDF5 file used to store data) e.g.
	 
		# config.py
		output_dir = '/Users/username/Documents/airports_data/
		hdf_path = '{}/airline_data.h5'.format(output_dir)

2. run the script `airports.data.get_flight_data.py` to download flight level data files. Input the years you would like to include in the variable `years`. The resulting csv files will be saved in `output_dir`
3. Download the weather files needed using your browser or otherwise from the ftp server using this url: [ftp://ftp.ncdc.noaa.gov/pub/data/ghcn/daily/by_year/2016.csv.gz](ftp://ftp.ncdc.noaa.gov/pub/data/ghcn/daily/by_year/{year}.csv.gz). Be sure to replace {year} with the desired year of data
4. Unzip these files by running `airports.data.get_weather_data.py`
5. Add the flight level data and weather data to the HDF5 store by running script `airports.data.csv_to_hdf5.py` (again specifying the variable `years`)
6. To obtain the aircraft level data file, use the scraper by running the script: `airports.data.get_plane_level_data.py`. This will create an xlsx file `plane_info.xlsx` in `output_dir` using all Tail numbers available from the flight level data now stored in the HDF5 store.
7. Finally run the script `airports.data.merge_data.py`. This will use the `geopy` module to merge daily weather data onto the flight data. It will then merge all needed data files into a single flatfile. If memory is an issue, this process can be altered to use chunking

## Predicting flight delays 

* See the ipdbviewer for an ample of how this data can be used