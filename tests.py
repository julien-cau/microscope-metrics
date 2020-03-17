
# import configuration parser
from metrics.utils.utils import MetricsConfig

# import logging
import logging

# import Argolight analysis tools
from metrics.samples.argolight import analyze_spots, analyze_resolution

# import other sample types analysis tools

# TODO: these imports should go somewhere else in the future
import imageio
from metrics.interface import omero
from credentials import HOST, PORT, USER, PASSWORD, GROUP

# TODO: these constants should go somewhere else in the future. Basically are recovered by OMERO scripting interface
RUN_MODE = 'local'
# RUN_MODE = 'omero'

spots_image_id = 7
vertical_stripes_image_id = 3
horizontal_stripes_image_id = 5
spots_image_path = '/Users/julio/PycharmProjects/OMERO.metrics/Images/201702_RI510_Argolight-1-1_010_SIR_ALX.dv/201702_RI510_Argolight-1-1_010_SIR_ALX_THR.ome.tif'
vertical_stripes_image_path = '/Users/julio/PycharmProjects/OMERO.metrics/Images/201702_RI510_Argolight-1-1_004_SIR_ALX.dv/201702_RI510_Argolight-1-1_004_SIR_ALX_THR.ome.tif'
horizontal_stripes_image_path = '/Users/julio/PycharmProjects/OMERO.metrics/Images/201702_RI510_Argolight-1-1_005_SIR_ALX.dv/201702_RI510_Argolight-1-1_005_SIR_ALX_THR.ome.tif'
config_file = 'my_microscope_config.ini'


# Creating logging services
logger = logging.getLogger('metrics')
logger.setLevel(logging.DEBUG)

# create file handler which logs even debug messages
fh = logging.FileHandler('metrics.log')
fh.setLevel(logging.ERROR)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)


def get_local_data(path):
    raw_img = imageio.volread(path)
    logger.info(f'Reading image {path}')
    pixel_sizes = (0.039, 0.039, 0.125)
    pixel_units = 'MICRON'

    return {'image_data': raw_img, 'pixel_sizes': pixel_sizes, 'pixel_units': pixel_units}


def get_omero_data(image_id):
    conn = omero.open_connection(username=USER,
                                 password=PASSWORD,
                                 group=GROUP,
                                 port=PORT,
                                 host=HOST)

    image = omero.get_image(conn, image_id)
    raw_img = omero.get_5d_stack(image)
    pixel_sizes = omero.get_pixel_sizes(image)
    pixel_units = omero.get_pixel_units(image)

    conn.close()

    return {'image_data': raw_img, 'pixel_sizes': pixel_sizes, 'pixel_units': pixel_units}


def main(run_mode):
    logger.info('Metrics started')

    config = MetricsConfig()
    config.read(config_file)

    if run_mode == 'local':
        spots_image = get_local_data(spots_image_path)
        vertical_res_image = get_local_data(vertical_stripes_image_path)
        horizontal_res_image = get_local_data(horizontal_stripes_image_path)

    elif run_mode == 'omero':
        spots_image = get_omero_data(spots_image_id)
        vertical_res_image = get_omero_data(vertical_stripes_image_id)
        horizontal_res_image = get_omero_data(horizontal_stripes_image_id)

    else:
        raise Exception('run mode not defined')

    if config.has_section('ARGOLIGHT'):
        logger.info(f'Running analysis on Argolight samples')
        al_conf = config['ARGOLIGHT']
        if al_conf.getboolean('do_spots'):
            logger.info(f'Analyzing spots image...')
            analyze_spots(spots_image['image_data'],
                          spots_image['pixel_sizes'],
                          low_corr_factors=al_conf.getlistfloat('low_threshold_correction_factors'),
                          high_corr_factors=al_conf.getlistfloat('high_threshold_correction_factors'))

        if al_conf.getboolean('do_vertical_res'):
            logger.info(f'Analyzing vertical resolution...')
            analyze_resolution(vertical_res_image['image_data'],
                               vertical_res_image['pixel_sizes'],
                               vertical_res_image['pixel_units'],
                               2)

        if al_conf.getboolean('do_horizontal_res'):
            logger.info(f'Analyzing horizontal resolution...')
            analyze_resolution(horizontal_res_image['image_data'],
                               horizontal_res_image['pixel_sizes'],
                               horizontal_res_image['pixel_units'],
                               1)

        logger.info('Metrics finished')


if __name__ == '__main__':
    main(RUN_MODE)
