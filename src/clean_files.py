#!/usr/bin/python
###############################################################################
# Delete all the files in the a particular subfolder (such as the 'proc' or 
# 'orig' subfolder) for each landsat image folder within a given folder.
###############################################################################

import os
import sys
import shutil
import re
import datetime
import csv
import argparse # Requires Python 2.7 or above

def main(subfolder='proc'):
    parser = argparse.ArgumentParser(description='Delete all files in each "%s" subfolder containing locally processed Landsat imagery'%subfolder)
    parser.add_argument("in_folder", metavar="in", type=str, default=None,
            help='Path to the base folder containing a set of folders with extracted Landsat surface reflectance images')
    parser.add_argument("--subfolder", type=str, default='proc',
            help='Subfolder to clear of files and folders (such as "proc" or "orig")')
    args = parser.parse_args()

    in_folder = args.in_folder
    if not os.path.exists(in_folder):
        raise IOError(in_folder + ' does not exist')

    subfolder = args.subfolder

    landat_image_folder_re = re.compile('^[0-9]{4}_[0-9]{3}_((LT4)|(LT5)|(LE7))$')
    landsatfile_re = re.compile('^(lndsr.)?((LT4)|(LT5)|(LE7))[0-9]{13}[A-Z]{3}[0-9]{2}.hdf$')
    Landsat4_re = re.compile('LT4$')
    Landsat5_re = re.compile('LT5$')
    Landsat7_re = re.compile('LE7$')

    data_array = []

    choice = raw_input('Warning - all files and folders within any "%s" subfolders for Landsat images in '%subfolder + in_folder + ' will be deleted. To continue, type "YES" and hit enter:\n')
    if choice != 'YES':
        print 'Cancelled.'
        return

    for outer_item in os.listdir(in_folder):
        # First cycle through the yearly folders
        outer_item_full = os.path.join(in_folder, outer_item)
        orig_folder = os.path.join(outer_item_full, 'orig')
        proc_folder = os.path.join(outer_item_full, 'proc')
        if not landat_image_folder_re.match(outer_item) or not os.path.isdir(orig_folder):
            continue
        else:
            subfolder_path = os.path.join(outer_item_full, subfolder)
            if not os.path.exists(subfolder_path):
                print subfolder_path + ' does not exist'
                continue
            subfolder_items = os.listdir(subfolder_path)
            if len(subfolder_items) >= 1:
                for subfolder_item in subfolder_items:
                    if os.path.isdir((os.path.join(subfolder_path, subfolder_item))):
                        shutil.rmtree(os.path.join(subfolder_path, subfolder_item))
                    else:
                        os.remove(os.path.join(outer_item_full, subfolder, subfolder_item))
                print 'Deleted %s file(s) and/or folder(s) in '%len(subfolder_items) + subfolder_path
            else:
                print 'No files or folders in ' + subfolder_path

if __name__ == "__main__":
    sys.exit(main())
