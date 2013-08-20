library(rgdal)
library(raster)
library(rgeos) # for 'gBuffer' function
library(ggplot2)
library(gridExtra) # for 'unit' function
library(plyr) # for 'join' function

image_list <- read.csv('H:/Data/TEAM/VB/Rasters/Landsat/image_list.csv')
zoi <- readOGR('H:/Data/TEAM/VB/Shapefiles', 'VB_ZOI_GEO')

lin_stretch <- function(image, pct=2) {
    # Applies linear stretch (2 percent by default). Assumes image is arranged 
    # with bands in columns. Returns the image with stretch applied and bands 
    # rescaled to range from 0 - 1.
    if ((pct < 0) | pct > 100) {
        stop('pct must be > 0 and < 100')
    }
    for (n in 1:ncol(image)) {
        pct2 <- quantile(image[, n], prob=0 + pct/100, na.rm=TRUE)
        pct98 <- quantile(image[, n], prob=1 - pct/100, na.rm=TRUE)
        image[, n] <- (image[, n] - pct2) / pct98
        image[, n][image[, n] < 0] <- 0
        image[, n][image[, n] > 1] <- 1
    }
    return(image)
}

for (n in 1:nrow(image_list)) {
    base_in_file <- sub('.hdf$', '', image_list[n, ]$file_path)
    base_out_file <- sub('orig', 'proc', base_in_file)

    print(paste('Processing', base_in_file, sep=''))

    fc <- stack(paste(base_in_file, '_band4.bsq', sep=''),
                         paste(base_in_file, '_band3.bsq', sep=''),
                         paste(base_in_file, '_band2.bsq', sep=''))
    fc <- aggregate(fc, fact=2)
    fc_zoi <- spTransform(zoi, CRS(proj4string(fc)))
    fc_crop <- crop(fc, fc_zoi)
    fc_crop_masked <- mask(fc_crop, fc_zoi)

    year <- image_list[n, ]$year
    julian_day <- image_list[n, ]$julian_day
    sensor <- image_list[n, ]$sensor
    main_title <- paste(year, '-', sprintf("%03i", julian_day),
                        ' (', sensor, ')', sep='')
    sub_title <- as.character(image_list[n, ]$file)
    full_title <- substitute(atop(main_title, atop(sub_title)), 
                             list(main_title=main_title, sub_title=sub_title))

    # # Setup the zoi dataframe for ggplot2
    # fc_zoi@data$id <- rownames(fc_zoi@data)
    # fc_zoi.points <- fortify(fc_zoi, region="id")
    # fc_zoi.df <- join(fc_zoi.points, fc_zoi@data, by="id")

    # Setup the false color raster matrix for ggplot2, and apply a linear 2 
    # percent stretch
    fc_matrix <- getValues(fc_crop_masked)
    fc_matrix <- lin_stretch(fc_matrix)
    fc_matrix[is.na(fc_matrix)] <- 1
    fc_df <- data.frame(x=coordinates(fc_crop_masked)[, 1],
                        y=coordinates(fc_crop_masked)[, 2],
                        rgb=rgb(fc_matrix))

    theme_set(theme_bw(base_size=8))
    ggplot(fc_df) +
        geom_raster(aes(x, y, fill=rgb)) + coord_fixed() + 
        scale_fill_identity() + 
        labs(title=full_title) +
        theme(axis.text.x=element_blank(), axis.text.y=element_blank(),
              axis.title.x=element_blank(), axis.title.y=element_blank(),
              panel.background=element_blank(), panel.border=element_blank(),
              panel.grid.major=element_blank(), panel.grid.minor=element_blank(),
              plot.background=element_blank(), axis.ticks=element_blank(),
              plot.margin=unit(c(.1, .1, .1, .1), 'cm'))
        #geom_path(data=fc_zoi.df, aes(long, lat), color='blue', size=1)
    ggsave(paste(base_out_file, '_browse_image.png', sep=''), width=3.25, 
           height=3.25, dpi=300)
}
