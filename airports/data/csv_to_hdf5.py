import pandas as pd
import numpy as np
import flyingpandas as fp
from airports.config import output_dir, hdf_path
from airports.helpers import get_hour
"""
Move the larger csvs to hdf5 with high compression to save disk space
"""

def flight_data_to_hdf(years):
    table_name = 'On_Time_On_Time_Performance'

    dtype = {
        'Year': np.float64,
        'Month': np.float64,
        'DayofMonth': np.float64,
        'DayOfWeek': np.float64,
        'TailNum': np.object,
        'UniqueCarrier': np.object,
        'Origin': np.object,
        'OriginState': np.object,
        'OriginCityName': np.object,
        'DepDelayMinutes': np.float64,
        'CRSDepTime': np.float64,
        'DepTime': np.object,
        'Cancelled': np.float64,
        'TaxiOut': np.float64,
        'Distance': np.float64,
        'AirTime': np.object,
        'CarrierDelay': np.float64,
        'WeatherDelay': np.float64,
        'NASDelay': np.float64,
        'SecurityDelay': np.float64,
        'LateAircraftDelay': np.float64,
        'Dest': np.object
    }

    keep_cols = dtype.keys()

    months = xrange(1, 12 + 1)
    store = pd.HDFStore(hdf_path)
    for y in years:
        for m in months:
            filename = '{}_{}_{}.csv'.format(table_name, y, m)
            source = '{}/{}'.format(output_dir, filename)

            try:
                df = pd.read_csv(source, dtype=dtype)
                df = df[keep_cols]
                store.append(table_name, df, index=False,
                             format='table', data_columns=True,
                             complevel=9, complib='blosc')
                print 'data added to hdf5 store for {}'.format(filename)
            except IOError:
                print 'no file for {}'.format(filename)

    store.close()


def weather_data_to_hdf(filename):
    header = ['station_identifier', 'date', 'observation_type', 'observation_value']
    df = pd.read_csv(output_dir + filename, header=None)
    df = df.iloc[:, :4]
    df.columns = header

    df = df.pivot_table(index=['station_identifier', 'date'],
                        columns='observation_type', values='observation_value')
    df.reset_index(inplace=True)

    # PRCP = Precipitation (tenths of mm, inches to hundredths on Daily Form pdf file)
    # SNOW = Snowfall (mm, inches to tenths on Daily Form pdf file)
    # SNWD = Snow depth (mm, inches on Daily Form pdf file)
    # TMAX = Maximum temperature ***
    # TMIN = Minimum temperature ***
    # FMTM = Time of fastest mile or fastest 1-minute wind (hours and minutes, i.e., HHMM)

    # Keep only the five core weather types
    header.remove('observation_type')
    header.remove('observation_value')
    df = df[header + ['PRCP', 'SNOW', 'SNWD', 'TMAX', 'TMIN']]

    # convert date str to datetime
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')

    # store in hdfstore
    with pd.HDFStore(hdf_path) as store:
        store.append('weather_data', df, index=False,
                     format='table', data_columns=True,
                     complevel=9, complib='blosc')

if __name__ == '__main__':
    years = [2013, 2014]  # xrange(2000, 2015 + 1)
    flight_data_to_hdf(years)

    weather_data_to_hdf('weather_2013.csv')
    weather_data_to_hdf('weather_2014.csv')
