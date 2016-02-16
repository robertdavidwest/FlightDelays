import pandas as pd
from airports.config import hdf_path, output_dir
from airports.helpers import fix_for_hdf

url = lambda tailnum: 'http://registry.faa.gov/aircraftinquiry/NNum_Results.aspx?NNumbertxt={}'.format(tailnum)


def convert_tbl_to_df(tbl):
    """reshape raw data from html table into a singe series dataframe"""

    tbl_pt1 = tbl.iloc[:, 0:2]
    tbl_pt1.columns = ['key', 'value']
    tbl_pt2 = tbl.iloc[:, 2:4]
    tbl_pt2.columns = ['key', 'value']
    
    df = tbl_pt1.append(tbl_pt2)
    df = df.dropna(how='any')
    df.index = df['key']
    df.drop(axis=1, labels='key', inplace=True)
    return df


def get_plane_level_info(tailnums):
    """return a dataframe of plane level info from :
            http://registry.faa.gov/aircraftinquiry/
       given a list of tailnumbers
    """

    all_info = pd.DataFrame()
    for i, tailnum in enumerate(tailnums):
        try:
            tables = pd.read_html(url(tailnum))
        except ValueError:
            print '{} no data'.format(tailnum)
            continue

        try:
            # for simplicity sake we will only pick up aircrafts that
            # have a single assigned tailnum
            # (there is info available for deregistered and historical registration)
            status = tables[1].iloc[0,0]
        except KeyError:
            print '{} no data'.format(tailnum)
            continue

        if not isinstance(status, unicode):
            continue
        if 'is Assigned' not in status:
            print '{} not assigned'.format(tailnum)
            continue

        plane_info = tables[3]
        airworthiness = tables[5]

        plane_info = convert_tbl_to_df(plane_info)
        airworthiness = convert_tbl_to_df(airworthiness)

        all = plane_info.append(airworthiness)
        all = all.dropna(how='any')
        df_one_row = pd.DataFrame(data=[all['value']])


        df_one_row['TailNum'] = tailnum

        all_info = all_info.append(df_one_row)
        print 'tail num {}: {} added to frame'.format(i+1, tailnum)

    return all_info


if __name__ == '__main__':

    store = pd.HDFStore(hdf_path)
    flight_data = store.select('On_Time_On_Time_Performance', columns=['TailNum'])
    tailnums = flight_data['TailNum'].drop_duplicates()

    print 'there are {} unique tailnumbers in the dataset'.format(len(tailnums))
    all_plane_info = get_plane_level_info(tailnums)

    all_plane_info = fix_for_hdf(all_plane_info)

    # remove '/' from variable names
    all_plane_info.columns = [c.replace('/','') for c in all_plane_info.columns]

    store.append('plane_info', all_plane_info, index=False,
                 format='table', data_columns=True,
                 complevel=9, complib='blosc')

    # back up csv
    all_plane_info.to_csv(output_dir + 'plane_info.csv', index=False)