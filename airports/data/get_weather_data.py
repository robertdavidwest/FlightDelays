import gzip
from airports.config import output_dir

weather_zip_filename = '2013.csv.gz'
zip_file_loc = output_dir + '/' + weather_zip_filename
file = gzip.open(zip_file_loc, 'rb')
outFile = open(output_dir + '/weather_' + weather_zip_filename[:-3], 'wb')
outFile.write(file.read())
file.close()
outFile.close()
