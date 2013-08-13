###############################################################################
# Script to output a CSV file listing Landsat images for a given TEAM site.  
# Only works if the Landsat files are organized in a directory hierarchy by 
# year and then by Julian day.
###############################################################################

import os
import re
import datetime
import csv

source_dir = 'H:/Data/TEAM/VB/Rasters/Landsat_7'
output_dir = 'H:/Data/TEAM/VB/Rasters/Landsat_7'
output_file = 'Landsat_images.csv'

year_re = re.compile('^[12][90][78901][0-9]$')
julian_re = re.compile('^[0123][0-9]{2}$')
landsatfile_re = re.compile('^(lndsr.)?L[ET][57][0-9]{13}[A-Z]{3}[0-9]{2}.hdf$')
satellite_re = re.compile('L[ET][57]')

data_array = []

for outer_path in os.listdir(source_dir):
    # First cycle through the yearly folders
    full_outer_path = os.path.join(source_dir, outer_path)
    if year_re.match(outer_path) and os.path.isdir(full_outer_path):
        year = outer_path
    else:
        continue
    for inner_path in os.listdir(full_outer_path):
        # Now cycle through the Julian day folders. The original images are 
        # stored in a 'orig' subfolder under the Julian folder.
        full_orig_path = os.path.join(full_outer_path, inner_path, 'orig')
        if julian_re.match(inner_path) and os.path.isdir(full_orig_path):
            julian = inner_path
            for file in os.listdir(full_orig_path):
                full_file_path = os.path.join(full_orig_path, file)
                if os.path.isfile(full_file_path) and landsatfile_re.match(file):
                    satellite = satellite_re.search(file).group()
                    # Below is from http://bit.ly/17khclI
                    dt = datetime.datetime.strptime(year + julian, '%Y%j')
                    tt = dt.timetuple()
                    data_array.append({'file': file,
                                       'file_path': full_file_path,
                                       'year': year,
                                       'satellite': satellite,
                                       'julian_day': julian,
                                       'month': tt.tm_mon,
                                       'day': tt.tm_mday})

fieldnames = ['year', 'julian_day', 'month', 'day', 'satellite', 'file', 'file_path']
output_fid = open(os.path.join(output_dir, output_file), 'wb')
csvwriter = csv.DictWriter(output_fid, fieldnames=fieldnames)
csvwriter.writeheader()
for row in data_array:
    csvwriter.writerow(row)
output_fid.close()
