from io import BytesIO

import numpy as np
import os
from PIL import Image
import rasterio as rio
from owslib.wms import WebMapService

import src.utils.settings as settings


class RemoteSensingLocalData:
    def __init__(self,
                dop_dir,
                epsg_code,
                clip_border):
        """
        | Constructor method

        :param str dop_dir: TODO
        :param int epsg_code: epsg code of the coordinate reference system
        :param bool clip_border: if True, the image size is increased by the border size
        :returns: None
        :rtype: None
        """
        self.dop_dir = dop_dir
        self.epsg_code = epsg_code
        self.clip_border = clip_border

    def get_image(self, tif_file):
        """
        | Returns an image given its coordinates of the top left corner.

        :returns: image
        """
        tif_path = os.path.join(self.dop_dir, tif_file)
        image = np.asarray(Image.open(tif_path), dtype=np.float32)

        return image

    def get_top_left_coordinate(self, tif_file):
        """
        Returns the coordintate element of the tif file.

        :returns: coordinates (x, y)
        """
        tif_path = os.path.join(self.dop_dir, tif_file)
        img = rio.open(tif_path)
        bbox = img.bounds
        return (int(bbox.left), int(bbox.top))


class RemoteSensingDataDownloader:
    def __init__(self,
                 wms_url,
                 wms_layer,
                 epsg_code,
                 clip_border):
        """
        | Constructor method

        :param str wms_url: url of the web map service
        :param str wms_layer: layer of the web map service
        :param int epsg_code: epsg code of the coordinate reference system
        :param bool clip_border: if True, the image size is increased by the border size
        :returns: None
        :rtype: None
        """
        self.wms = WebMapService(wms_url)
        self.wms_layer = wms_layer
        self.epsg_code = epsg_code
        self.clip_border = clip_border

    def get_bounding_box(self, coordinates):
        """
        | Returns the bounding box of a tile given its coordinates of the top left corner.

        :param (int, int) coordinates: coordinates (x, y)
        :returns: bounding_box (x_1, y_1, x_2, y_2)
        :rtype: (int, int, int, int)
        """
        if self.clip_border:
            bounding_box = (coordinates[0] - settings.BORDER_SIZE_METERS,
                            coordinates[1] - settings.IMAGE_SIZE_METERS - settings.BORDER_SIZE_METERS,
                            coordinates[0] + settings.IMAGE_SIZE_METERS + settings.BORDER_SIZE_METERS,
                            coordinates[1] + settings.BORDER_SIZE_METERS)
        else:
            bounding_box = (coordinates[0],
                            coordinates[1] - settings.IMAGE_SIZE_METERS,
                            coordinates[0] + settings.IMAGE_SIZE_METERS,
                            coordinates[1])
        return bounding_box

    def get_response(self, bounding_box):
        """
        | Wrapper of owslib.wms.WebMapService.getmap().read()
        | Returns a response (byte stream) of the web map service given its bounding box.

        :param (int, int, int, int) bounding_box: bounding_box (x_1, y_1, x_2, y_2)
        :returns: response
        :rtype: bytes
        """
        response = self.wms.getmap(layers=[self.wms_layer],
                                   srs=f'EPSG:{self.epsg_code}',
                                   bbox=bounding_box,
                                   format='image/tiff',
                                   size=(settings.IMAGE_SIZE + 2 * settings.BORDER_SIZE
                                         if self.clip_border else settings.IMAGE_SIZE,
                                         settings.IMAGE_SIZE + 2 * settings.BORDER_SIZE
                                         if self.clip_border else settings.IMAGE_SIZE),
                                   bgcolor='#000000').read()
        return response

    def get_image(self, coordinates):
        """
        | Returns an image given its coordinates of the top left corner.

        :param (int, int) coordinates: coordinates (x, y)
        :returns: image
        :rtype: np.ndarray[np.uint8]
        """
        bounding_box = self.get_bounding_box(coordinates)
        response = self.get_response(bounding_box)

        with Image.open(BytesIO(response)) as file:
            # noinspection PyTypeChecker
            image = np.array(file, dtype=np.uint8)

        return image
