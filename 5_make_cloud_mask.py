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
