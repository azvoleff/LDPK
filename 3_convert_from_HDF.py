import os
import sys
import csv
import re
import argparse # Requires Python 2.7 or above

import numpy as np

from osgeo import gdal
from osgeo import osr

def main():
    parser = argparse.ArgumentParser(description='Convert a list of Landsat HDF files to the default ENVI binary format (band sequential).')
    parser.add_argument("image_list_file", metavar="image_list", type=str, default=None,
            help='Path to a CSV file listing Landsat images (in format output from catalog_Landsat.py)')
    args = parser.parse_args()

    image_list_file = args.image_list_file
    if not os.path.isfile(image_list_file):
        raise IOError('image_list must be a CSV file')

    image_list = []
    with open(image_list_file, 'rb') as f:
        reader = csv.DictReader(f)
        for row in reader:
            image_list.append(row)
    f.close()

    bandname_re = re.compile('[a-zA-Z0-9_-]*$')
    for image in image_list:
        image_path = image['file_path']
        image_base_path, ext = os.path.splitext(image_path)
        image_basename, ext = os.path.splitext(image['file'])
        print 'Processing %s'%image_path

        gdal_dataset = gdal.Open(image_path)
        SubDatasets = [x[0] for x in gdal_dataset.GetSubDatasets()]
        for SubDataset in SubDatasets:
            ds = gdal.Open(SubDataset)
            bandname = bandname_re.search(SubDataset).group()
            dst_path = os.path.join(image_base_path + '_' + bandname + '.bsq')
            if os.path.isfile(dst_path):
                print 'Skipping %s - file already exists'%dst_path
                continue
            src_band_array = ds.GetRasterBand(1).ReadAsArray()
            driver = gdal.GetDriverByName('ENVI')
            geo = ds.GetGeoTransform()  # get the datum of the original image
            proj = ds.GetProjection()   # get the projection of the original image
            print 'Writing %s'%bandname
            dst_ds = driver.CreateCopy(dst_path, ds)
            dst_band = dst_ds.GetRasterBand(1)
            dst_band.WriteArray(src_band_array)
            dst_ds.SetGeoTransform(geo) # set the datum for the output image
            dst_ds.SetProjection(proj)  # set the projection for the output image
            dst_ds = None

if __name__ == "__main__":
    sys.exit(main())
