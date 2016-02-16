from geopy.distance import vincenty
import pandas as pd
import numpy as np
import flyingpandas as fp
from airports.config import output_dir, hdf_path
from airports.helpers import fix_for_hdf

def show_dups(df, cols):
    """display duplicates rows"""
    idx = df.duplicated(cols, keep='first') | df.duplicated(cols, keep='last')
    dups = df[idx]
    dups = dups.sort_values(cols)
    print dups


def get_airports():
    airports = pd.read_excel(output_dir + 'airports new.xlt')

    show_dups(airports, 'iata')
    # after a quick investigation online it appears as though
    # - the Code for 'Moriarty' airport should be "0E0"
    # - the Code for 'Crownpoint' airport should be "0E8"
    # Looks like these changed to zeros because of excels 'scientific' number formatting
    # fix bad iata codes
    def fix_code(df, airport, correct_code):
        idx = df['airport'] == airport
        if sum(idx) > 1:
            raise AssertionError('more than one {} airport'.format(airport))
        df.loc[idx, 'iata'] = correct_code
        return df

    airports = fix_code(airports, airport='Moriarty', correct_code='0E0')
    airports = fix_code(airports, airport='Crownpoint', correct_code='0E8')
    show_dups(airports, 'iata')

    return airports


def get_carriers():
    carriers = pd.read_excel(output_dir + 'carriers.xls')
    show_dups(carriers, 'Code')
    carriers = carriers.dropna(how='all')
    carriers.rename(inplace=True, columns={
        'Code': 'UniqueCarrier',
        'Description': 'CarrierName'
    })
    return carriers


def get_airport_weather_stations():
    """find the closest weather station to each airport. Then daily weather
    can easily be merged onto flight data by day and airport variables

    if the closest station is further away than `min_distance` then a message
    will be displayed
    """
    min_distance = 50  # miles
    stations = pd.read_excel(output_dir + 'station_geo_info.xlsx')
    airports = get_airports()

    def get_distince(row, airport_location):
            """calculate distance from station to airport.
            if vincenty alg fails to converge, enter nan value"""
            row_location = (row['LATITUDE'], row['LONGITUDE'])
            try:
                return vincenty(airport_location, row_location).miles
            except ValueError:
                return np.nan

    # for each airport, find the closest weather station
    airport_stations = pd.DataFrame()
    for i, row in airports.iterrows():
        airport_location = (row['lat'], row['long'])

        # calculate distance of all stations to airport
        stations['airport_to_station'] = stations.apply(lambda row:
            get_distince(row, airport_location), axis=1
        )

        # find the closest station and store info as a 1 row df
        idxmin = stations['airport_to_station'].idxmin(skipna=True)
        closest_station = stations.iloc[idxmin, :]
        for c in row.index:
            closest_station[c] = row[c]
        closest_station = pd.DataFrame(data=[closest_station])

        # ensure station is within minimum distinance
        if closest_station['airport_to_station'].values > min_distance:
            print 'For airport {}, the closest station is {} miles away'.format(
                row['airport'], closest_station['airport_to_station'].values
            )
        airport_stations = airport_stations.append(closest_station)
        print '{} out of {} stations found, ' \
              'Current distance {} miles'.format(i,
                                                 len(airports),
                                                 closest_station['airport_to_station'].values)

    airport_stations.rename(inplace=True, columns={
        'lat': 'airport_lat',
        'long': 'airport_long',
        'LATITUDE': 'station_lat',
        'LONGITUDE': 'station_long',
        'ELEVATION': 'station_elevation',
        'NAME': 'station_name'
    })
    return airport_stations


if __name__ == '__main__':
    airport_and_stations_from_csv = True
    store = pd.HDFStore(hdf_path)

    # it takes a while to find the closest airport weather station <->
    # to airports so ideally this will only be run once even if I need to
    # re-run other things in this script

    if airport_and_stations_from_csv:
        airport_stations = pd.read_csv(output_dir + 'airport_stations.csv')
    else:
        airport_stations = get_airport_weather_stations()

        #airport_stations = pd.to_csv(output_dir + 'airport_stations.csv', index=False)
        #airport_stations = fix_for_hdf(airport_stations)
        #store.append('airport_and_stations', airport_stations, index=False,
        #             format='table', data_columns=True,
        #             complevel=9, complib='blosc')

    # merge in weather station identifiers to flatfile
    def merge_airport_stations(data, origin_or_dest):
        rename_dict = {
            'iata': origin_or_dest,
            'station_identifier': origin_or_dest + '_' + 'station_identifier',
            'airport_to_station': origin_or_dest + '_' + 'airport_to_station'
        }
        df = airport_stations[rename_dict.keys()].rename(columns=rename_dict)
        data = fp.merge('m:1', data, df, on=origin_or_dest, how='left')
        return data

    data = store['On_Time_On_Time_Performance']
    data = merge_airport_stations(data, 'Origin')
    data = merge_airport_stations(data, 'Dest')

    # merge in carrier names to flights dataset
    carriers = get_carriers()
    data = fp.merge('m:1', data, carriers, on='UniqueCarrier', how='left')

    # merge in plane level info
    plane_info = pd.read_csv(output_dir + 'plane_info.csv')
    plane_info = plane_info[[
        'Engine Model',	'MFR Year',	'Manufacturer Name', 'Model', 'TailNum'
    ]]
    data = fp.merge('m:1', data, plane_info, on='TailNum', how='left')

    # create flight date

    # this is slow but will run, the below commented out .apply was breaking
    FlightDate = []
    for i, row in data.iterrows():
        print '{} of {}'.format(i, len(data))
        year=int(row['Year'])
        month=int(row['Month'])
        day=int(row['DayofMonth'])
        flight_date = pd.datetime(year, month, day)
        FlightDate.append(flight_date)
    data['FlightDate'] = FlightDate

    '''
    data['FlightDate'] = data.apply(lambda df:
        pd.datetime(year=int(df['Year']),
                    month=int(df['Month']),
                    day=int(df['DayofMonth']))
    )
    '''
    # merge in origin and destination weather information by date and weather
    # station
    weather = store['weather_data']

    def merge_weather(data, origin_or_dest):
        data = fp.merge('m:1', data, weather,
                        left_on=['FlightDate',
                                 '{}_station_identifier'.format(origin_or_dest)],
                        right_on=['date', 'station_identifier'],
                        how='left')

        data.rename(columns={'PRCP': '{}PRCP'.format(origin_or_dest),
                             'SNOW': '{}SNOW'.format(origin_or_dest),
                             'SNWD': '{}SNWD'.format(origin_or_dest),
                             'TMAX': '{}TMAX'.format(origin_or_dest),
                             'TMIN': '{}TMIN'.format(origin_or_dest)},
                    inplace=True)
        data = data.drop(axis=1, labels=['date', 'station_identifier'])
        return data

    data = merge_weather(data, 'Origin')
    data = merge_weather(data, 'Dest')
    try:
        data = fix_for_hdf(data)
        # store flatfile
        store.append('flat_file', data, index=False,
                     format='table', data_columns=True,
                     complevel=9, complib='blosc')
    except:
        import ipdb; ipdb.set_trace()
    store.close()

