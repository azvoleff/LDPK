import os
import sys
import csv
import re
import argparse # Requires Python 2.7 or above

import numpy as np

from osgeo import gdal
from osgeo import osr

def subdataset_search(SubDatasets, search_string):
    """
    Returns the file location for the first subdataset in a GDAL dataset that 
    has a given string in its name.
    """
    SubDatasets_list = [x[0] for x in SubDatasets]
    band_name = [x for x in SubDatasets_list if search_string in x]
    return band_name[0]

def main():
    parser = argparse.ArgumentParser(description='Convert a list of Landsat HDF files to the default ENVI binary format (band sequential).')
    parser.add_argument("image_list_file", metavar="image_list", type=str, default=None,
            help='Path to a CSV file listing Landsat images (in format output from catalog_Landsat.py)')
    args = parser.parse_args()

    bands = ['band1', 'band2', 'band3', 'band4', 'band5', 'band7']

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

        in_ds = gdal.Open(image_path)
        SubDatasets = [x[0] for x in in_ds.GetSubDatasets()]

        # Setup the destination raster
        dst_path = os.path.join(image_base_path + '_bands.bsq')
        driver = gdal.GetDriverByName('ENVI')
        # if os.path.isfile(dst_path):
        #     print 'Skipping %s - file already exists'%dst_path
        #     continue
        # Load the band1 subdataset to pull the georeferencing from it
        band1_ds = gdal.Open(subdataset_search(in_ds.GetSubDatasets(), 'band1'))
        dst_ds = driver.Create(dst_path, band1_ds.RasterXSize, band1_ds.RasterYSize, 6, gdal.GDT_Float32)
        src_srs = osr.SpatialReference()
        src_srs.ImportFromWkt(band1_ds.GetProjectionRef())
        # Setup output spatial reference
        # Make CRS user name:
        CRS_user_name = 'WGS_1984_UTM_Zone_' + str(src_srs.GetUTMZone())
        if src_srs.GetUTMZone() > 0: CRS_user_name += 'N'
        else: CRS_user_name += 'S'
        dst_srs = osr.SpatialReference()
        dst_srs.SetProjCS(CRS_user_name)
        dst_srs.SetWellKnownGeogCS('WGS84')
        dst_srs.SetUTM(src_srs.GetUTMZone())
        dst_ds.SetProjection(dst_srs.ExportToWkt())
        dst_ds.SetMetadata(in_ds.GetMetadata())
        band1 = None

        # Note that band_num is the band index in the NEW raster
        band_num = 1
        for SubDataset in SubDatasets:
            bandname = bandname_re.search(SubDataset).group()
            if not bandname in bands:
                continue
            print 'Writing %s'%bandname
            in_sub_ds = gdal.Open(SubDataset)
            # TODO: Fix the below check to work properly
            # if not in_sub_ds.GetProjectionRef() == dst_ds.GetProjectionRef():
            #     raise IOError('all input bands must have same projection system')
            src_band = in_sub_ds.GetRasterBand(1)
            src_band_array = src_band.ReadAsArray()
            # Write the data to the new raster
            dst_band = dst_ds.GetRasterBand(band_num)
            dst_band.WriteArray(src_band_array)
            dst_band.SetMetadata(in_sub_ds.GetMetadata())
            dst_band.SetDescription(dst_band.GetMetadataItem('long_name'))
            in_sub_ds = None
            band_num += 1
        dst_band = None
        dst_ds = None

        # Calculate combined cloud mask
        print 'Writing cloud mask'
        cloud_QA_ds = gdal.Open(subdataset_search(in_ds.GetSubDatasets(), 'cloud_QA'))
        cloud_QA = cloud_QA_ds.GetRasterBand(1).ReadAsArray()
        cloud_shadow_QA_ds = gdal.Open(subdataset_search(in_ds.GetSubDatasets(), 'cloud_shadow_QA'))
        cloud_shadow_QA = cloud_shadow_QA_ds.GetRasterBand(1).ReadAsArray()
        adjacent_cloud_QA_ds = gdal.Open(subdataset_search(in_ds.GetSubDatasets(), 'adjacent_cloud_QA'))
        adjacent_cloud_QA = adjacent_cloud_QA_ds.GetRasterBand(1).ReadAsArray()
        cloud_mask = np.zeros(np.shape(cloud_QA))
        cloud_mask[cloud_QA == 255] = 255
        cloud_mask[cloud_shadow_QA == 255] = 255
        cloud_mask[adjacent_cloud_QA == 255] = 255
        # Write combined cloud mask
        cloud_path = os.path.join(image_base_path + '_cloud_mask.bsq')
        driver = gdal.GetDriverByName('ENVI')
        cloud_ds = driver.CreateCopy(cloud_path, cloud_QA_ds)
        cloud_ds.SetProjection(dst_srs.ExportToWkt())
        cloud_ds.SetMetadata(in_ds.GetMetadata())
        cloud_band = cloud_ds.GetRasterBand(1)
        cloud_band.WriteArray(cloud_mask)
        cloud_ds = None

        # Write missing data file
        print 'Writing fill_QA file'
        fill_QA_ds = gdal.Open(subdataset_search(in_ds.GetSubDatasets(), 'fill_QA'))
        fill_QA = fill_QA_ds.GetRasterBand(1).ReadAsArray()
        fill_path = os.path.join(image_base_path + '_fill_mask.bsq')
        driver = gdal.GetDriverByName('ENVI')
        fill_ds = driver.CreateCopy(fill_path, fill_QA_ds)
        fill_ds.SetProjection(dst_srs.ExportToWkt())
        fill_ds.SetMetadata(in_ds.GetMetadata())
        fill_band = fill_ds.GetRasterBand(1)
        fill_band.WriteArray(fill_QA)
        fill_ds = None

        in_ds = None

if __name__ == "__main__":
    sys.exit(main())
