import os
import sys
import csv
import re

import numpy as np

from osgeo import gdal
from osgeo import osr

base_path = 'H:/Data/TEAM/'
site_code = 'VB'

image_list_file = os.path.join(base_path, site_code, 'Rasters', 'Landsat_7', 'VB_Landsat_7.csv')
zoi_shape = os.path.join(base_path, site_code, 'Shapefiles', site_code + '_ZOI_GEO')

image_list = []
with open(image_list_file, 'rb') as f:
    reader = csv.DictReader(f)
    for row in reader:
        image_list.append(row)

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
        print bandname
        src_band_array = ds.GetRasterBand(1).ReadAsArray()
        dst_path = os.path.join(image_base_path + '_' + bandname + '.bsq')
        driver = gdal.GetDriverByName('ENVI')
        geo = ds.GetGeoTransform()  # get the datum of the original image
        proj = ds.GetProjection()   # get the projection of the original image
        dst_ds = driver.CreateCopy(dst_path, ds)
        dst_band = dst_ds.GetRasterBand(1)
        dst_band.WriteArray(src_band_array)
        dst_ds.SetGeoTransform(geo) # set the datum for the output image
        dst_ds.SetProjection(proj)  # set the projection for the output image
        dst_ds = None
