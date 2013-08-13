import os
import re

import tarfile

tarfile_re = re.compile('^.*.tar.gz(ip)?$')
file_date_re = re.compile('^L[ET][57][0-9]{13}')

source_dir = 'H:/Data/TEAM/VB/Rasters/Landsat_7/ORIGINALS'
output_base = 'H:/Data/TEAM/VB/Rasters/Landsat_7'

for file in os.listdir(source_dir):
    file_path = os.path.join(source_dir, file)
    if not tarfile_re.match(file) or not os.path.isfile(file_path):
        print 'Skipping "%s". Not a valid file type.'%file_path
        continue
    metadata_string = file_date_re.match(file).group()
    year = metadata_string[-7:-3]
    julian_day = metadata_string[-3:]
    if not os.path.exists(os.path.join(output_base, year)):
        os.mkdir(os.path.join(output_base, year))
    if not os.path.exists(os.path.join(output_base, year, julian_day)):
        os.mkdir(os.path.join(output_base, year, julian_day))
    else:
        print 'Skipping "%s". Output dir "%s" already exists'%(file_path, os.path.join(output_base, year, julian_day))
        continue
    tar = tarfile.open(file_path)
    tar.extractall(os.path.join(output_base, year, julian_day, 'orig'))
    tar.close()
