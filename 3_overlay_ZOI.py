import os
import csv

from mpl_toolkits.basemap import Basemap
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.patches import Polygon

from osgeo import gdal
from osgeo import osr

base_path = 'H:/Data/TEAM/'
site_code = 'VB'

image_list_file = os.path.join(base_path, site_code, 'Rasters', 'Landsat_7', 'VB_Landsat_7.csv')
zoi_shape = os.path.join(base_path, site_code, 'Shapefiles', site_code + '_ZOI_GEO')

def reproject_dataset(dataset, pixel_factor=1, epsg_to=4326):
    """
    A sample function to reproject and resample a GDAL dataset from within 
    Python. The idea here is to reproject from one system to another, as well
    as to change the pixel size. The procedure is slightly long-winded, but
    goes like this:
    1. Set up the two Spatial Reference systems.
    2. Open the original dataset, and get the geotransform
    3. Calculate bounds of new geotransform by projecting the UL corners 
    4. Calculate the number of pixels with the new projection & spacing
    5. Create an in-memory raster dataset
    6. Perform the projection

    From: http://bit.ly/1a1XVKF
    """
    g = gdal.Open(dataset)
    geo_t = g.GetGeoTransform()
    x_size = g.RasterXSize
    y_size = g.RasterYSize

    src_sr = osr.SpatialReference()
    src_sr.ImportFromWkt(g.GetProjection())
    dst_sr = osr.SpatialReference()
    dst_sr.ImportFromEPSG(epsg_to)
    tx = osr.CoordinateTransformation(src_sr, dst_sr)
    # Work out the boundaries of the new dataset in the target projection
    (ulx, uly, ulz) = tx.TransformPoint(geo_t[0], geo_t[3])
    (lrx, lry, lrz) = tx.TransformPoint(geo_t[0] + geo_t[1]*x_size, \
            geo_t[3] + geo_t[5]*y_size)

    xpixel_spacing = ((lrx - ulx) / x_size) * pixel_factor
    ypixel_spacing = ((uly - lry) / y_size) * pixel_factor

    # Now, we create an in-memory raster
    mem_drv = gdal.GetDriverByName('MEM')
    # The size of the raster is given the new projection and pixel spacing
    # Using the values we calculated above. Also, setting it to store one band
    # and to use Float32 data type.
    dest = mem_drv.Create('', int((lrx - ulx)/xpixel_spacing), \
            int((uly - lry)/ypixel_spacing), 1, gdal.GDT_Float32)
    # Calculate the new geotransform
    new_geo = (ulx, xpixel_spacing, geo_t[2], uly, geo_t[4], -ypixel_spacing)
    # Set the geotransform
    dest.SetGeoTransform(new_geo)
    dest.SetProjection(dst_sr.ExportToWkt())
    # Perform the projection/resampling 
    res = gdal.ReprojectImage(g, dest, src_sr.ExportToWkt(), \
            dst_sr.ExportToWkt(), gdal.GRA_Bilinear)
    return dest

def plot_gdal_band(input_dataset):
    "Adapted from: http://bit.ly/1a1XVKF"
    #plt.figure ( figsize=(11.3*0.8, 8.7*0.8), dpi=600 ) # This is A4. Sort of
    geo = input_dataset.GetGeoTransform()
    XSize = input_dataset.RasterXSize
    YSize = input_dataset.RasterYSize
    data = input_dataset.ReadAsArray()
    data = np.flipud(data)
    data = np.ma.masked_values(data, 0)
    # These are the extents in the native raster coordinates
    extent = [geo[0], geo[0] + XSize*geo[1], \
            geo[3], geo[3] + YSize*geo[5]]
    map = Basemap(llcrnrlon=extent[0], llcrnrlat=extent[3], \
            urcrnrlon=extent[1], urcrnrlat=extent[2], lat_0=0, lon_0=-87, \
            projection='tmerc')
    map.imshow(data, cmap=cm.Greys_r, interpolation='nearest')
    map.drawmapboundary()
    return map

def plot_gdal_rgb(input_datasets):
    geo = input_datasets[0].GetGeoTransform()
    XSize = input_datasets[0].RasterXSize
    YSize = input_datasets[0].RasterYSize
    b = input_datasets[0].ReadAsArray()
    g = input_datasets[1].ReadAsArray()
    r = input_datasets[2].ReadAsArray()
    b = np.ma.masked_values(b, 0)
    g = np.ma.masked_values(g, 0)
    r = np.ma.masked_values(r, 0)
    data = np.dstack((b, g, r))
    data = np.flipud(data)

    # These are the extents in the native raster coordinates
    extent = [geo[0], geo[0] + XSize*geo[1], \
            geo[3], geo[3] + YSize*geo[5]]
    map = Basemap(llcrnrlon=extent[0], llcrnrlat=extent[3], \
            urcrnrlon=extent[1], urcrnrlat=extent[2], lat_0=0, lon_0=-87, \
            projection='tmerc')
    map.imshow(data, interpolation='nearest')
    return map

image_list = []
with open(image_list_file, 'rb') as f:
    reader = csv.DictReader(f)
    for row in reader:
        image_list.append(row)

def subdataset_index(search_string, SubDatasets):
    '''
    Returns the file location for the first subdataset with a given string in 
    its name.
    '''
    SubDatasets_list = [x[0] for x in SubDatasets]
    band_name = [x for x in SubDatasets_list if search_string in x]
    return band_name[0]

for image in image_list:
    image_path = image['file_path']
    gdal_dataset = gdal.Open(image_path)
    band_list = gdal_dataset.GetSubDatasets()

    g_reproj = reproject_dataset(subdataset_index('band2', band_list))
    r_reproj = reproject_dataset(subdataset_index('band3', band_list))
    nir_reproj = reproject_dataset(subdataset_index('band4', band_list))

    #m = plot_gdal_rgb((g_reproj, r_reproj, nir_reproj))
    m = plot_gdal_band((g_reproj))
    m.readshapefile(zoi_shape, 'ZOI')
    plt.title('%s - %s/%s/%s\n%s'%(site_code, image['year'], 
            image['month'], image['day'], image['file']))
    # Recolor ZOI boundary:
    for xy in m.ZOI:
        poly = Polygon(xy, color='red', alpha=0.4)
        plt.gca().add_patch(poly)
    #plt.show()
    plot_file = '%s_%s%02i%02i_%s.png'%(site_code, image['year'], 
            int(image['month']), int(image['day']), image['file'])
    plt.savefig(plot_file)
    plt.clf()
