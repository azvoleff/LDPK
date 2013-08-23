###############################################################################
# Script to output a CSV file listing Landsat images for a given TEAM site.  
###############################################################################

import os
import sys
import re
import datetime
import csv
import argparse # Requires Python 2.7 or above

def main():
    parser = argparse.ArgumentParser(description='Catalog a folder of Landsat images and save the list to a CSV file')
    parser.add_argument("in_folder", metavar="in", type=str, default=None,
            help='Path to a folder of extracted HDF format Landsat surface reflectance images')
    parser.add_argument("--out_file", metavar="out", type=str, 
            default=None, help='Filename for output CSV file')
    args = parser.parse_args()

    in_folder = args.in_folder
    if not args.out_file:
        out_file = os.path.join(args.in_folder, 'image_list.csv')

    landat_image_folder_re = re.compile('^[0-9]{4}_[0-9]{3}_((LT4)|(LT5)|(LE7))$')
    landsatfile_re = re.compile('^(lndsr.)?((LT4)|(LT5)|(LE7))[0-9]{13}[A-Z]{3}[0-9]{2}.hdf$')
    Landsat4_re = re.compile('LT4$')
    Landsat5_re = re.compile('LT5$')
    Landsat7_re = re.compile('LE7$')

    data_array = []

    for outer_item in os.listdir(in_folder):
        # First cycle through the yearly folders
        outer_item_full = os.path.join(in_folder, outer_item)
        orig_folder = os.path.join(outer_item_full, 'orig')
        if not landat_image_folder_re.match(outer_item) or not os.path.isdir(orig_folder):
            continue
        year = outer_item[0:4]
        julian_day = outer_item[5:8]
        for inner_item in os.listdir(orig_folder):
            inner_item_full = os.path.join(orig_folder, inner_item)
            # Check to ensure inner item is a Landsat HDF file
            if os.path.isdir(inner_item_full) or not landsatfile_re.match(inner_item):
                continue
            if Landsat4_re.search(outer_item):
                sensor = 'LT4'
            elif Landsat5_re.search(outer_item):
                sensor = 'LT5'
            elif Landsat7_re.search(outer_item):
                sensor = 'LE7'
            else:
                print 'Skipping "%s". Cannot determine sensor from folder name.'%outer_item
                continue
            # Below is from http://bit.ly/17khclI
            dt = datetime.datetime.strptime(year + julian_day, '%Y%j')
            tt = dt.timetuple()
            data_array.append({'file': inner_item,
                               'file_path': inner_item_full,
                               'year': year,
                               'sensor': sensor,
                               'julian_day': julian_day,
                               'month': tt.tm_mon,
                               'day': tt.tm_mday})

    fieldnames = ['year', 'julian_day', 'month', 'day', 'sensor', 'file', 'file_path']
    out_fid = open(out_file, 'wb')
    csvwriter = csv.DictWriter(out_fid, fieldnames=fieldnames)
    csvwriter.writeheader()
    for row in data_array:
        csvwriter.writerow(row)
    out_fid.close()

if __name__ == "__main__":
    sys.exit(main())
