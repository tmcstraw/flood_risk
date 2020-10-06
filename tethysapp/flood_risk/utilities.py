from django.http import JsonResponse, HttpResponse, Http404
import fiona
import os
import glob
from shapely.geometry import MultiPolygon, Point, shape, mapping, LineString, Polygon, MultiLineString
from .utilities import *
from osgeo import ogr, osr
from pyproj.crs import CRS
import json
from .app import FloodRisk as app
from collections import OrderedDict
import rasterio
import rasterstats as rs
import geopandas as gpd
import numpy as np
from .config import USER_DIR
from geopandas.tools import sjoin
import geojson
from tethys_sdk.gizmos import MapView, MVLayer, MVView

def centroid(coordinates):
    x = (coordinates[0]+coordinates[2])/2
    y = (coordinates[1]+coordinates[3])/2
    return [x, y]

"""
Function to make a directory if it does not exist and change directories
"""
def mk_change_directory(file_name):
    SHP_DIR = USER_DIR + file_name + '/'
    SHP_DIR = os.path.join(SHP_DIR, '')
    try:
        os.mkdir(SHP_DIR)
    except OSError:
        print("Creation of the directory %s failed" % SHP_DIR)
    else:
        print("Successfully created the directory %s " % SHP_DIR)
    os.chdir(SHP_DIR)


"""
Function to find file of specified file type in directory
"""
def find_file(file_name, ending):
    SHP_DIR = USER_DIR + file_name + '/'
    for file in os.listdir(SHP_DIR):
        # Reading the output shapefile only
        if file.endswith(ending):
            file_path = os.path.join(SHP_DIR, file)
            return file_path

"""
Function to move files to user directory and get field names
"""
def move_files_get_fields(shapefile, file_name, filetype):
    SHP_DIR = USER_DIR+file_name+'/'

    mk_change_directory(file_name)

    # Remove existing files in directory
    files = glob.glob(SHP_DIR+'*')
    for f in files:
        os.remove(f)

    field_list = []
    return_obj = {}

    for f in shapefile:
        f_name = f.name
        f_path = os.path.join(SHP_DIR, f_name)

        with open(f_path, 'wb') as f_local:
            f_local.write(f.read())

    for file in os.listdir(SHP_DIR):
        # Reading the shapefile only
        if file.endswith(filetype):
            f_path = os.path.join(SHP_DIR, file)

            ds = ogr.Open(f_path)
            lyr = ds.GetLayer()

            field_names = [field.name for field in lyr.schema]

            for field in field_names:
                field_list.append(field)

    return_obj["field_names"] = field_list
    return_obj = json.dumps(return_obj)

    return return_obj

"""
Function to move files to user workspace
"""
def move_files(shapefile, file_name):
    SHP_DIR = USER_DIR + file_name + '/'

    mk_change_directory(file_name)

    # Remove existing files in directory
    files = glob.glob(SHP_DIR + '*')
    for f in files:
        os.remove(f)

    # Iterate over files and add to user workspace
    for f in shapefile:
        f_name = f.name
        f_path = os.path.join(SHP_DIR, f_name)

        with open(f_path, 'wb') as f_local:
            f_local.write(f.read())

    return JsonResponse({"success": "success"})

"""
Function to move files to geoserver
"""
def move_geoserver(file_name):
    GEOSERVER_URI = 'http://www.example.com/flood-risk'
    WORKSPACE = 'flood-risk'

    # Retrieve a geoserver engine
    geoserver_engine = app.get_spatial_dataset_service(name='main_geoserver', as_engine = True)

    # Check for workspace and create workspace for app if it doesn't exist
    response = geoserver_engine.list_workspaces()

    SHP_DIR = USER_DIR + file_name + '/'

    file_base = SHP_DIR+file_name

    mk_change_directory(file_name)

    if response['success']:
        workspaces = response['result']

        if WORKSPACE not in workspaces:
            geoserver_engine.create_workspace(workspace_id=WORKSPACE, uri=GEOSERVER_URI)

    # Upload shapefile to GeoServer
    store = ''.join(file_name)
    store_id = WORKSPACE +':' + store
    geoserver_engine.create_shapefile_resource(
        store_id=store_id,
        shapefile_base=file_base,
        overwrite=True
    )

"""
Convert polygon shapefile to lines shapefile
"""
def polygon_to_line(shapefile, file_name, id_field):
    not_empty_file = True

    # Set the working directory
    mk_change_directory(file_name)

    # Open the Buildings shapefile
    with fiona.open(shapefile) as source:
        this_schema = {'properties': OrderedDict([(id_field, 'float:19.11'),
                                                  ('Shape_Leng', 'float:19.11'),
                                                  ('Shape_Area', 'float:19.11'),
                                                  ('Index', 'float:19.11')]),
                       'geometry': ['LineString']}
        # Create a file to save the lines shapefile
        mk_change_directory("Building_Outlines")

        with fiona.open('Building_Outlines.shp', 'w', driver='ESRI Shapefile',
                        crs=source.crs, schema=this_schema) as output:
            index = 1
            # Iterate over the Polygons and MultiPolygons in the buildings shapefile
            for polys in source:
                if polys['geometry']['type'] == 'MultiPolygon':
                    multipolygon = shape(polys['geometry'])
                    polygon_list = list(multipolygon)
                    # Iterate over the Polygons in each MultiPolygon
                    for pol in polygon_list:
                        # Identify the boundary of each Polygon
                        boundary = pol.boundary
                        index = iterate_list(boundary, output, polys, index, id_field)
                elif polys['geometry']['type'] == 'Polygon':
                    # Identify the boundary of each Polygon
                    boundary = (shape(polys['geometry'])).boundary
                    index = iterate_list(boundary, output, polys, index, id_field)
            if not os.stat(find_file("Building_Outlines", ".shp")).st_size == 0:
                not_empty_file = False
                return not_empty_file

    return not_empty_file

"""
Function to buffer
"""
def add_buffer(objectid, buffer_val, first_file, second_file, output_geometry, geom_to_buffer):
    not_empty_file = True

    mk_change_directory(first_file)

    """
    # Reading in the lines shapefile
    input_file = find_file(first_file, ".shp")

    # Reading in the crs and converting
    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataset = driver.Open(input_file)
    layer = dataset.GetLayer()
    spatialRef = layer.GetSpatialRef()
    dc_crs = CRS.from_wkt(spatialRef.ExportToWkt())
    fio_crs = dc_crs.to_wkt()
    """

    # Read the input shapefile and buffer to output shapefile
    with fiona.open(find_file(first_file, ".shp"), 'r') as source:

        # Set the output file
        this_schema = {'properties': OrderedDict([(objectid, 'float:19.11'),
                                                  ('Shape_Leng', 'float:19.11'),
                                                  ('Shape_Area', 'float:19.11'),
                                                  ('Index', 'float:19.11')]),
                       'geometry': [output_geometry]}
        source_crs = source.crs

        # Create a directory for the output
        mk_change_directory(second_file)

        # Output buffered file
        with fiona.open(second_file + ".shp", 'w', driver='ESRI Shapefile',
                        crs=source_crs, schema=this_schema) as output:
            # Iterate over each line in line file
            index = 1
            for item in source:
                if item['geometry']['type'] == geom_to_buffer:
                    item_shape = shape(item['geometry'])
                    item_buffer = item_shape.buffer(float(buffer_val))

                    # Check area to make sure Building Polygon is hollow
                    if item_buffer.area > (item_buffer.length * (float(buffer_val) + 1)):
                        item_buffer = item_shape.buffer(0.1)
                        if item_buffer.area > (item_buffer.length * (float(buffer_val) + 1)):
                            item_buffer = item_shape.buffer(0.01)
                            if item_buffer.area > (item_buffer.length * (float(buffer_val) + 1)):
                                item_buffer = item_shape.buffer(0.001)
                                if item_buffer.area > (item_buffer.length * (float(buffer_val) + 1)):
                                    print("Filled polygon")

                    index = output_shape(item_buffer, output, item, index, objectid)
                else:
                    print(item['geometry']['type'])

            if not os.stat(find_file(second_file, ".shp")).st_size == 0:
                not_empty_file = False
    return not_empty_file

"""
Function which writes to shapefile
"""
def output_shape(oneline, output, line, index, objectid):
    output.write({'geometry': mapping(oneline),
                  'type': oneline.geom_type,
                  'properties': {objectid: line['properties'][objectid],
                                 'Shape_Leng': oneline.length,
                                 'Shape_Area': oneline.area,
                                 'Index': index}})
    index += 1
    return index

"""
Function to divide streets at set distances and output as shapefile
"""
def divide_lines(streetid, distance, file_name, output_file):
    mk_change_directory(file_name)

    # Reading in the lines shapefile
    line_file = find_file(file_name, ".shp")

    # Reading in the crs and converting
    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataset = driver.Open(line_file)
    layer = dataset.GetLayer()
    spatialRef = layer.GetSpatialRef()
    dc_crs = CRS.from_wkt(spatialRef.ExportToWkt())
    fio_crs = dc_crs.to_wkt()

    # Read the line shapefile and add a new field 'max_depth'
    with fiona.open(line_file, 'r') as source:

        # Set the output file
        this_schema = {'properties': OrderedDict([(streetid, 'float:19.11'),
                                                  ('Shape_Leng', 'float:19.11'),
                                                  ('Shape_Area', 'float:19.11'),
                                                  ('Index', 'float:19.11')]),
                       'geometry': ['LineString']}
        source_crs = fio_crs

        # Starting value for new index field
        index = 1

        # Create a directory for the output file
        mk_change_directory(output_file)

        # Output file for total street width
        with fiona.open((output_file + ".shp"), 'w', driver='ESRI Shapefile',
                        crs=source_crs, schema=this_schema) as output:
            # Iterate over each line in line file
            for line in source:
                if line['geometry']['type'] == "LineString":
                    line_shape = shape(line['geometry'])
                    multiline_list = split_line_with_points(line_shape, distance)
                    for oneline in multiline_list:
                        index = iterate_list(oneline, output, line, index, streetid)
                elif line['geometry']['type'] == 'MultiLineString':
                    line_shape = shape(line['geometry'])
                    line_shape_list = list(line_shape)
                    for lines in line_shape_list:
                        multiline_list = split_line_with_points(lines, distance)
                        for oneline in multiline_list:
                            index = iterate_list(oneline, output, line, index, streetid)


"""
Function called by identify_lines to iterate through a LineString list to output LineStrings
"""
def iterate_list(oneline, output, line, index, objectid):
    if oneline.type == "LineString":
        index = output_shape(oneline, output, line, index, objectid)
    elif oneline.type == "MultiLineString":
        for singleline in oneline:
            index = output_shape(singleline, output, line, index, objectid)
    return index

"""
Function to cut line at specified distance, returning two LineStrings
"""
def cut(line, distance):

    # Check that distance is within line
    if distance <= 0.0 or distance >= line.length:
        return[LineString(line)]

    # Cut line
    coords = list(line.coords)
    for i, p in enumerate(coords):
        pd = line.project(Point(p))
        if pd == distance:
            return [
                LineString(coords[:i+1]),
                LineString(coords[i:])]
        if pd > distance:
            cp = line.interpolate(distance)
            return [
                LineString(coords[:i] + [(cp.x, cp.y)]),
                LineString([(cp.x, cp.y)] + coords[i:])]

"""
Function to call cut function if sufficient length remaining in line
"""
def split_line_with_points(line, d):
    segments = []
    current_line = line
    d_current = d

    while True:
        if d_current < (line.length):
            seg, current_line = cut(current_line, d)
            segments.append(seg)
            d_current += d
        else:
            segments.append(current_line)
            break

    return segments

"""
Function to populate the Max Depth field based on raster data
"""
def max_intersect(input_shapefile, input_raster):
    return_obj = {}

    # Set the working directory
    mk_change_directory(input_shapefile)
    with fiona.open(find_file(input_shapefile, ".shp"), 'r') as polygon_file:
        mk_change_directory(input_raster)
        with rasterio.open(find_file(input_raster, ".tif")) as raster_file:

            transform = raster_file.transform
            transform.to_gdal()
            array = raster_file.read(1)
            array[array==0] = np.nan

            # Extract zonal stats
            raster_stats = rs.zonal_stats(polygon_file,
                                          array,
                                          all_touched=True,
                                          nodata=raster_file.nodata,
                                          affine=transform,
                                          geojson_out=True,
                                          raster_out=True,
                                          copy_properties=True,
                                          stats='max')

            # Add max depth to max depth field and export raster stats to a shapefile
            raster_stats_dataframe = gpd.GeoDataFrame.from_features(raster_stats)

            if not raster_stats_dataframe.empty:
                raster_stats_dataframe = raster_stats_dataframe.drop(columns=['mini_raster_array', 'mini_raster_affine', 'mini_raster_nodata'])
                raster_stats_dataframe.fillna(0, inplace=True)
                return_obj["return_dataframe"] = raster_stats_dataframe
                return_obj["is_dataframe_empty"] = False
            else:
                return_obj["is_dataframe_empty"] = True

    return return_obj
