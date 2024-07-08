import re
from collections import OrderedDict
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio as rio
import rasterio.features
import topojson as tp
from shapely.geometry import Polygon

import src.utils.settings as settings

pd.options.mode.chained_assignment = None


class Postprocessor:
    ATTRIBUTES = OrderedDict()
    ATTRIBUTES['class'] = 'str:7'
    CLASS_MAP = {1: 'Hochbau', 2: 'Tiefbau'}
    SCHEMA = {'properties': ATTRIBUTES,
              'geometry': 'Polygon'}

    def __init__(self,
                 output_dir_path,
                 bounding_box,
                 epsg_code,
                 boundary_gdf):
        """
        | Constructor method

        :param str or Path output_dir_path: path to the output directory
        :param (int, int, int, int) bounding_box: bounding box (x_1, y_1, x_2, y_2)
        :param int epsg_code: epsg code of the coordinate reference system
        :param gpd.GeoDataFrame or None boundary_gdf: boundary geodataframe
        :returns: None
        :rtype: None
        """
        self.tiles_dir_path = Path(output_dir_path) / 'cached_tiles'
        self.bounding_box = bounding_box
        self.epsg_code = epsg_code
        self.boundary_gdf = boundary_gdf

    def export_features(self,
                        features,
                        coordinates):
        """
        | Exports features of a tile as a shape file (.shp) in a subdirectory to the cached_tiles directory.
        | Each subdirectory name is in the following schema: x_y

        :param list[dict[str, dict[str, Any]]] features: features
        :param (int, int) coordinates: coordinates (x, y)
        :returns: None
        :rtype: None
        """
        sub_dir_path = self.tiles_dir_path / f'{coordinates[0]}_{coordinates[1]}'
        sub_dir_path.mkdir(exist_ok=True)

        for path in sub_dir_path.iterdir():
            path.unlink()

        if features:
            shape_file_path = sub_dir_path / f'{coordinates[0]}_{coordinates[1]}.shp'
            gdf = gpd.GeoDataFrame.from_features(features, crs=f'EPSG:{self.epsg_code}')
            gdf.to_file(str(shape_file_path), schema=Postprocessor.SCHEMA)

    def vectorize_mask(self,
                       mask,
                       coordinates,
                       res=None):
        """
        | Exports a shape file (.shp) of the polygons in the vectorized mask given its coordinates
            of the top left corner in a subdirectory to the cached_tiles directory.

        :param np.ndarray[np.uint8] mask: mask
        :param (int, int) coordinates: coordinates (x, y)
        :param float res: Resolution if default settings 0.2 m does not fit
        :returns: None
        :rtype: None
        """
        transform = rio.transform.from_origin(
            west=coordinates[0],
            north=coordinates[1],
            xsize=settings.RESOLUTION if res is None else res,
            ysize=settings.RESOLUTION if res is None else res,
        )
        vectorized_mask = rio.features.shapes(mask, transform=transform)

        features = [{'properties': {'class': Postprocessor.CLASS_MAP.get(int(value))}, 'geometry': shape}
                    for shape, value in vectorized_mask if int(value) != 0]
        self.export_features(features=features,
                             coordinates=coordinates)

    def concatenate_gdfs(self, coordinates):
        """
        | Returns a concatenated geodataframe.

        :param list[(int, int)] coordinates: coordinates (x, y) of each tile
        :returns: concatenated geodataframe
        :rtype: gpd.GeoDataFrame
        """
        gdfs = []

        pattern = re.compile(r'^(-?\d+)_(-?\d+)$')

        for path in self.tiles_dir_path.iterdir():
            match = pattern.search(path.name)
            if match:
                processed_coordinates = (int(match.group(1)), int(match.group(2)))
                if processed_coordinates in coordinates:
                    if any(path.iterdir()):
                        gdf_path = (self.tiles_dir_path / f'{processed_coordinates[0]}_{processed_coordinates[1]}' /
                                    f'{processed_coordinates[0]}_{processed_coordinates[1]}.shp')
                        gdf = gpd.read_file(gdf_path)
                        gdfs.append(gdf)

        concatenated_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs=f'EPSG:{self.epsg_code}')
        return concatenated_gdf

    @staticmethod
    def sieve_gdf(gdf, sieve_size):
        """
        | Returns a sieved geodataframe.

        :param gpd.GeoDataFrame gdf: geodataframe
        :param int sieve_size: sieve size in square meters (minimum area of polygons to retain)
        :returns: sieved geodataframe
        :rtype: gpd.GeoDataFrame
        """
        if gdf.empty:
            return gdf

        mask = gdf.area >= sieve_size
        sieved_gdf = gdf.loc[mask]
        sieved_gdf.reset_index(drop=True,
                               inplace=True)
        return sieved_gdf

    @staticmethod
    def fill_polygon(polygon, hole_size):
        """
        | Returns a polygon without holes.
        |
        | Based on:
        | https://gis.stackexchange.com/a/409398

        :param Polygon polygon: polygon
        :param int hole_size: hole size in square meters (maximum area of holes in the polygons to retain)
        :returns: filled polygon
        :rtype: Polygon
        """
        if polygon.interiors:
            interiors = []
            for interior in polygon.interiors:
                polygon_interior = Polygon(interior)
                if polygon_interior.area >= hole_size:
                    interiors.append(interior)
            return Polygon(polygon.exterior.coords, holes=interiors)
        else:
            return polygon

    @staticmethod
    def fill_gdf(gdf, hole_size):
        """
        | Returns a geodataframe without holes in the polygons.
        | The hole size of buildings is doubled.
        |
        | Based on:
        | https://gis.stackexchange.com/a/409398
        | https://stackoverflow.com/a/61466689

        :param gpd.GeoDataFrame gdf: geodataframe
        :param int hole_size: hole size in square meters (maximum area of holes in the polygons to retain)
        :returns: filled geodataframe
        :rtype: gpd.GeoDataFrame
        """
        if gdf.empty:
            return gdf

        gdf['geometry'] = gdf.apply(lambda x:
                                    Postprocessor.fill_polygon(x['geometry'],
                                                               hole_size=2 * hole_size)
                                    if x['class'] == 'Hochbau'
                                    else Postprocessor.fill_polygon(x['geometry'],
                                                                    hole_size=hole_size),
                                    axis=1)
        return gdf

    def simplify_gdf(self, gdf, res=None):
        """
        | Returns a geodataframe with simplified polygons (Douglas-Peucker algorithm is used).

        :param gpd.GeoDataFrame gdf: geodataframe
        :param float res: Resolution if default settings 0.2 m does not fit
        :returns: simplified geodataframe
        :rtype: gpd.GeoDataFrame
        """
        if gdf.empty:
            return gdf

        topo = tp.Topology(gdf, prequantize=False)
        resolution = settings.RESOLUTION if res is None else res
        simplified_gdf = topo.toposimplify(resolution).to_gdf(crs=f'EPSG:{self.epsg_code}')
        return simplified_gdf

    def clip_gdf(self, gdf):
        """
        | Returns a clipped geodataframe.

        :param gpd.GeoDataFrame gdf: geodataframe
        :returns: clipped geodataframe
        :rtype: gpd.GeoDataFrame
        """
        if self.boundary_gdf is not None:
            clipped_gdf = gpd.clip(gdf,
                                   mask=self.boundary_gdf,
                                   keep_geom_type=True)
        else:
            polygon_bounding_box = Polygon([[self.bounding_box[0], self.bounding_box[1]],
                                            [self.bounding_box[0], self.bounding_box[3]],
                                            [self.bounding_box[2], self.bounding_box[3]],
                                            [self.bounding_box[2], self.bounding_box[1]]])
            clipped_gdf = gpd.clip(gdf,
                                   mask=polygon_bounding_box,
                                   keep_geom_type=True)
        return clipped_gdf
