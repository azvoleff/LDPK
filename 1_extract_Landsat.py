import os
import sys
import re
import argparse # Requires Python 2.7 or above

import tarfile

def main():
    parser = argparse.ArgumentParser(description='Extract a folder of Landsat images and convert from HDF to the default ENVI binary format (band sequential).')
    parser.add_argument("in_folder", metavar="in", type=str, default=None,
            help='Path to a folder of .tar.gz Landsat surface reflectance images')
    parser.add_argument("out_folder", metavar="out", type=str, default=None,
            help='Output folder')
    args = parser.parse_args()

    in_folder = args.in_folder
    out_folder = args.out_folder

    tarfile_re = re.compile('^.*.tar.gz(ip)?$')
    file_date_re = re.compile('^((LT4)|(LT5)|(LE7))[0-9]{13}')
    Landsat4_re = re.compile('^LT4')
    Landsat5_re = re.compile('^LT5')
    Landsat7_re = re.compile('^LE7')

    for file in os.listdir(args.in_folder):
        file_path = os.path.join(args.in_folder, file)
        if not tarfile_re.match(file) or not os.path.isfile(file_path):
            print 'Skipping "%s". Not a valid file type.'%file_path
            continue
        # Figure out which satellite the image is from
        if Landsat4_re.match(file):
            sensor = 'LT4'
        elif Landsat5_re.match(file):
            sensor = 'LT5'
        elif Landsat7_re.match(file):
            sensor = 'LE7'
        else:
            print 'Skipping "%s". Cannot determine sensor from filename.'%file_path
            continue
        metadata_string = file_date_re.match(file).group()
        year = metadata_string[-7:-3]
        julian_day = metadata_string[-3:]
        this_out_folder = os.path.join(out_folder, '%s_%s_%s'%(year, julian_day, sensor))
        if not os.path.exists(this_out_folder):
            os.mkdir(this_out_folder)
        else:
            print 'Skipping "%s". Output dir "%s" already exists'%(file_path, this_out_folder)
            continue
        tar = tarfile.open(file_path)
        print 'Extracting %s to %s'%(file, this_out_folder)
        tar.extractall(os.path.join(this_out_folder, 'orig'))
        if not os.path.exists(os.path.join(this_out_folder, 'proc')):
            os.mkdir(os.path.join(this_out_folder, 'proc'))
        tar.close()

if __name__ == "__main__":
    sys.exit(main())
