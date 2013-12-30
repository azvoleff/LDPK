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
    parser.add_argument("image_list_file", metavar="image_list", type=str, 
            default=None,
            help='Path to a CSV file listing Landsat images (in format output from catalog_Landsat.py)')
    args = parser.parse_args()

    bands = ['band1', 'band2', 'band3', 'band4', 'band5', 'band7',
             'adjacent_cloud_QA', 'cloud_shadow_QA', 'cloud_QA', 'fill_QA']
    # num_new_bands is used in creating the output file to allow for the
    # extra data quality bands (the combined cloud mask and total missing 
    # masks).
    num_new_bands = 2

    image_list_file = args.image_list_file
    base, ext = os.path.splitext(image_list_file)
    if not ext.lower() == '.csv':
        raise IOError('image_list must be a csv file')
    if not os.path.isfile(image_list_file):
        raise IOError('%s not found'%image_list_file)

    image_list = []
    with open(image_list_file, 'rb') as f:
        reader = csv.DictReader(f)
        for row in reader:
            image_list.append(row)
    f.close()

    bandname_re = re.compile('[a-zA-Z0-9_-]*$')
    for image in image_list:
        image_path = image['file_path']
        print 'Processing %s'%image_path

        # Figure out the output filename, saving the output in a 'proc' folder 
        # (for processed) in the folder one above the 'orig' folder that the 
        # original images are stored in.
        image_base, ext = os.path.splitext(image_path)
        in_base_path, in_base_filename = os.path.split(image_base)
        in_prefix, orig_dir = os.path.split(in_base_path)
        if orig_dir != 'orig':
            raise IOError('Folder layout does not match folder structure')
        out_path = os.path.join(in_prefix, 'proc')
        if not os.path.exists(out_path):
            os.mkdir(out_path)
        out_image_filename = in_base_filename + '.bsq'
        out_metadata_filename = in_base_filename + '.txt'
        dst_image_file = os.path.join(out_path, out_image_filename)
        dst_metadata_file = os.path.join(out_path, out_metadata_filename)

        in_ds = gdal.Open(image_path)
        SubDatasets = [x[0] for x in in_ds.GetSubDatasets()]

        # Setup the destination raster
        driver = gdal.GetDriverByName('ENVI')
        # if os.path.isfile(dst_image_file):
        #     print 'Skipping %s - file already exists'%dst_image_file
        #     continue
        # Load the band1 subdataset to pull the georeferencing from it
        band1_ds = gdal.Open(subdataset_search(in_ds.GetSubDatasets(), 'band1'))
        band1 = band1_ds.GetRasterBand(1)
        dst_ds = driver.Create(dst_image_file, band1_ds.RasterXSize, 
                band1_ds.RasterYSize, len(bands) + num_new_bands, band1.DataType)
        src_srs = osr.SpatialReference()
        src_gt = band1_ds.GetGeoTransform()
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
        dst_ds.SetGeoTransform(src_gt)
        band1_ds = None
        band1 = None

        # Also dump the main HDF metadata to a text file:
        metadata_fid = open(dst_metadata_file, 'w')
        metadata = in_ds.GetMetadata()
        metadata_fid.write('item,value\n')
        for key, value in metadata.items():
            metadata_fid.write('"' + key + '","' + value + '"\n')
        metadata_fid.close()

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
            long_band_name = dst_band.GetMetadataItem('long_name').replace(' ', '_')
            dst_band.SetDescription(long_band_name)
            NoDataValue = dst_band.GetMetadataItem('_FillValue')
            if NoDataValue: dst_band.SetNoDataValue(float(NoDataValue))
            in_sub_ds = None
            band_num += 1
            src_band = None
            dst_band = None

        # Calculate combined cloud mask
        print 'Calculating cloud mask'
        cloud_QA_ds = gdal.Open(subdataset_search(in_ds.GetSubDatasets(), 'cloud_QA'))
        cloud_QA = cloud_QA_ds.GetRasterBand(1).ReadAsArray()
        cloud_shadow_QA_ds = gdal.Open(subdataset_search(in_ds.GetSubDatasets(), 'cloud_shadow_QA'))
        cloud_shadow_QA = cloud_shadow_QA_ds.GetRasterBand(1).ReadAsArray()
        cloud_shadow_QA_ds = None
        adjacent_cloud_QA_ds = gdal.Open(subdataset_search(in_ds.GetSubDatasets(), 'adjacent_cloud_QA'))
        adjacent_cloud_QA = adjacent_cloud_QA_ds.GetRasterBand(1).ReadAsArray()
        adjacent_cloud_QA_ds = None
        cloud_mask = np.ones(np.shape(cloud_QA))
        cloud_mask[cloud_QA == 255] = 1
        cloud_mask[cloud_shadow_QA == 255] = 1
        cloud_mask[adjacent_cloud_QA == 255] = 1
        # Write combined cloud mask
        print 'Writing cloud mask'
        cloud_band = dst_ds.GetRasterBand(band_num)
        cloud_band.WriteArray(cloud_mask)
        cloud_band.SetMetadata(cloud_QA_ds.GetMetadata())
        cloud_band.SetDescription('combined_cloud_mask')
        NoDataValue = cloud_band.GetMetadataItem('_FillValue')
        if NoDataValue: cloud_band.SetNoDataValue(float(NoDataValue))
        band_num += 1
        cloud_QA_ds = None

        # Calculate combined cloud mask
        print 'Calculating total missing data (cloud and SLC gaps)'
        fill_QA_ds = gdal.Open(subdataset_search(in_ds.GetSubDatasets(), 'fill_QA'))
        fill_QA = fill_QA_ds.GetRasterBand(1).ReadAsArray()
        missing_mask = np.ones(np.shape(fill_QA))
        missing_mask[fill_QA == 255] = 1
        print 'Writing total missing data (cloud and SLC gaps)'
        missing_band = dst_ds.GetRasterBand(band_num)
        missing_band.WriteArray(missing_mask)
        missing_band.SetMetadata(fill_QA_ds.GetMetadata())
        missing_band.SetDescription('missing_mask')
        NoDataValue = missing_band.GetMetadataItem('_FillValue')
        if NoDataValue: missing_band.SetNoDataValue(float(NoDataValue))
        band_num += 1
        fill_QA_ds = None

        in_ds = None
        dst_ds = None

if __name__ == "__main__":
    sys.exit(main())
