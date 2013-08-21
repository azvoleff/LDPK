import os
import sys
import csv
import re
import argparse # Requires Python 2.7 or above

import numpy as np

from osgeo import gdal
from osgeo import osr

def main():
    parser = argparse.ArgumentParser(description='Catalog a folder of Landsat images and save the list to a CSV file')
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
        hdf_base, hdf_ext = os.path.splitext(image_path)
        orig_base_dir, image_base_name = os.path.split(hdf_base)
        print 'Processing %s'%image_base_name

        # Make cloud mask
        cloud_QA_ds = gdal.Open(hdf_base + '_cloud_QA.bsq')
        cloud_QA = cloud_QA_ds.GetRasterBand(1).ReadAsArray()
        cloud_shadow_QA_ds = gdal.Open(hdf_base + '_cloud_shadow_QA.bsq')
        cloud_shadow_QA = cloud_shadow_QA_ds.GetRasterBand(1).ReadAsArray()
        adjacent_cloud_QA_ds = gdal.Open(hdf_base + '_adjacent_cloud_QA.bsq')
        adjacent_cloud_QA = adjacent_cloud_QA_ds.GetRasterBand(1).ReadAsArray()

        cloud_mask = np.zeros(np.shape(cloud_QA))
        cloud_mask[cloud_QA == 255] = 255
        cloud_mask[cloud_shadow_QA == 255] = 255
        cloud_mask[adjacent_cloud_QA == 255] = 255

        # Save results under \proc rather than \orig:
        base_dir, orig = os.path.split(orig_base_dir)
        proc_base_dir = os.path.join(base_dir, 'proc')
        if not os.path.exists(proc_base_dir): os.mkdir(proc_base_dir)

        dst_path = os.path.join(proc_base_dir, image_base_name + '_comb_cloud_mask.bsq')
        driver = gdal.GetDriverByName('ENVI')
        geo = cloud_QA_ds.GetGeoTransform()  # get the datum of the original image
        proj = cloud_QA_ds.GetProjection()   # get the projection of the original image
        dst_ds = driver.CreateCopy(dst_path, cloud_QA_ds)
        dst_band = dst_ds.GetRasterBand(1)
        dst_band.WriteArray(cloud_mask)
        dst_ds.SetGeoTransform(geo) # set the datum for the output image
        dst_ds.SetProjection(proj)  # set the projection for the output image

        cloud_QA_ds = None
        cloud_shadow_QA_ds = None
        adjacent_cloud_QA_ds = None
        dst_ds = None

if __name__ == "__main__":
    sys.exit(main())
