library(rgdal)
library(raster)
library(rgeos) # needed for gBuffer function

image_list <- read.csv('H:/Data/TEAM/VB/Rasters/Landsat/image_list.csv')
zoi <- readOGR('H:/Data/TEAM/VB/Shapefiles', 'VB_ZOI_GEO')

mask_ZOI <- function(img, zoi, bufferwidth=1000) {
    zoi <- spTransform(zoi, CRS(proj4string(img)))
    # Buffer the ZOI so that cloud fill algorithms can have room to work when 
    # interpolating missing data
    zoi_buffer <- gBuffer(zoi, width=bufferwidth)
    img_crop <- crop(img, zoi_buffer)
    img_crop_mask <- mask(img_crop, zoi_buffer)
}

band_names <- list('band1', 'band2', 'band3', 'band4', 'band5', 'band6', 
                   'band7')
band_names <- list('band1')

image_list$pct_cloud <- NA
image_list$pct_missing <- NA

#for (n in 1:nrow(image_list)) {
for (n in 1:1) {
    base_in_file <- sub('.hdf$', '', image_list[n, ]$file_path)
    base_out_file <- sub('orig', 'proc', base_in_file)

    for (band in band_names) {
        b <- raster(paste(base_in_file, '_', band, '.bsq', sep=''))
        b_masked <- mask_ZOI(b, zoi)
        writeRaster(b_masked,
                    paste(base_out_file, band, 'zoi_crop', sep='_'), 
                    format='ENVI')
    }

    fill_QA <- raster(paste(base_in_file, '_fill_QA.bsq', sep=''))
    fill_QA_masked <- mask_ZOI(fill_QA, zoi)
    writeRaster(fill_QA_masked,
                paste(base_out_file, '_fill_QA_crop', sep=''), format='ENVI')
    fill_QA_masked_stats <- table(getValues(fill_QA_masked))
    image_list$pct_missing[n] <- 100 - as.numeric(fill_QA_masked_stats['0'] / 
                                                  sum(fill_QA_masked_stats) * 
                                                  100)
     
    cloud <- raster(paste(base_out_file, '_comb_cloud_mask.bsq', sep=''))
    cloud_crop_masked <- mask_ZOI(cloud, zoi)
    writeRaster(cloud_crop_masked,
                paste(base_out_file, '_comb_cloud_mask_crop', sep=''), 
                format='ENVI')
    cloud_crop_masked_stats <- table(getValues(cloud_crop_masked))
    image_list$pct_cloud[n] <- as.numeric(cloud_crop_masked_stats['255'] / 
                                          sum(cloud_crop_masked_stats) * 100)
}
