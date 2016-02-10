import requests, zipfile, StringIO

# download and unzip all flight data from 1987 through 2015 and save in 
# outputdir
output_dir = 
years = xrange(1987, 2015 + 1)
months = xrange(1, 12 + 1)
for y in years:
    for m in months:
        zip_file_url = 'http://tsdata.bts.gov/PREZIP/'\
                       'On_Time_On_Time_Performance_{}_{}.zip'.format(y, m)
        r = requests.get(zip_file_url)
        if r.status_code == 200:
            z = zipfile.ZipFile(StringIO.StringIO(r.content))
            z.extractall(path=output_dir)