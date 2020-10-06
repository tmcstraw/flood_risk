from django.http import JsonResponse, HttpResponse, Http404
from tethys_sdk.gizmos import *
from .utilities import *
import geopandas as gpd
from geopandas.tools import sjoin
import math
from pyproj import Proj, transform
from django.shortcuts import render, reverse
import geojson
import fiona
import shutil
from .config import USER_DIR

def file_upload(request):
    return_obj = {}

    if request.is_ajax() and request.method == 'POST':

        filetype = request.POST["filetype"]
        file_name = request.POST["file_name"]
        shapefiles = request.FILES.getlist('shapefile')

        field_names = move_files_get_fields(shapefiles, file_name, filetype)
        field_names = json.loads(field_names)
        return_obj["field_names"] = field_names["field_names"]

        return JsonResponse(return_obj)

def file_upload_move_files(request):
    return_obj = {}

    if request.is_ajax() and request.method == 'POST':

        file_name = request.POST["file_name"]
        shapefiles = request.FILES.getlist('shapefile')

        move_files(shapefiles, file_name)

        return_obj['success'] = "success"

        return JsonResponse(return_obj)

def file_download(request):
    return_obj = {}

    # Get source folder
    file_name = request.POST["file_name"]
    SHP_DIR = USER_DIR + file_name + '/'

    # Get destination folder
    pathname = os.path.expanduser('~/Downloads/') + file_name + '/'

    #Copy source to destination
    try:
        shutil.copytree(SHP_DIR, pathname)
    except:
        print("File already downloaded")
        try:
            pathname = pathname[:-1]+'_copy/'
            shutil.copytree(SHP_DIR, pathname)
        except:
            print("File already downloaded")
            try:
                pathname = pathname[:-1] + '_copy/'
                shutil.copytree(SHP_DIR, pathname)
            except:
                print("File already downloaded")

    return_obj['file_path'] = pathname
    return JsonResponse(return_obj)

"""
Ajax controller which finds land use fields in shapefile
"""
def residential_landuse(request):
    return_obj = {}

    if request.is_ajax() and request.method == 'POST':
        filetype = request.POST["filetype"]
        file_name = request.POST["file_name"]
        landuse_field = request.POST["landuse_field"]

        f_path = find_file(file_name, filetype)
        landuse_file = gpd.read_file(f_path)
        landuse_file.fillna(0, inplace=True)
        landuse_file = landuse_file.rename(columns={landuse_field: 'landuse'})
        residential = landuse_file.landuse.unique()

        landuse_residential = []
        for use in residential:
            landuse_residential.append(use)
        print(landuse_residential)

        # residential = json.loads(landuse_residential)
        return_obj["residential"] = landuse_residential

    return JsonResponse(return_obj)


"""
Ajax controller which imports building shapefiles to the user workspace
"""
def building_process(request):
    return_obj = {}

    if request.is_ajax() and request.method == 'POST':

        # Import text entries and field names
        residential_landuse = request.POST["residential_landuse"]
        buffer_val = request.POST["buffer"]
        buildingid_field = request.POST["buildingid_field"]
        taxid_field = request.POST["taxid_field"]
        tax_field = request.POST["tax_field"]
        landuseid_field = request.POST["landuseid_field"]
        landuse_field = request.POST["landuse_field"]
        depth_0 = float(request.POST["depth_0"])
        depth_1 = float(request.POST["depth_1"])
        depth_2 = float(request.POST["depth_2"])
        depth_3 = float(request.POST["depth_3"])
        bldg_0 = (float(request.POST["bldg_0"])/100)
        bldg_1 = (float(request.POST["bldg_1"])/100)
        bldg_2 = (float(request.POST["bldg_2"])/100)
        bldg_3 = (float(
            request.POST["bldg_3"])/100)


        # Output building boundaries from building polygons shapefile
        f_path = find_file("bldg_file", ".shp")
        is_line_empty = polygon_to_line(f_path, "bldg_file", str(buildingid_field))
        if not is_line_empty:
            # Buffer lines shapefile to create polygons
            is_buffer_empty = add_buffer(str(buildingid_field), float(buffer_val), 'Building_Outlines', 'Bldg_Outline_Polygons', 'Polygon', 'LineString')

            if not is_buffer_empty:
                # Add max depth from raster to building boundary lines

                max_int_results = max_intersect("Bldg_Outline_Polygons", "depth_file")
                if not max_int_results['is_dataframe_empty']:
                    raster_stats_dataframe = max_int_results['return_dataframe']
                    raster_stats_dataframe['Max_Depth'] = raster_stats_dataframe['max']
                    raster_stats_dataframe = raster_stats_dataframe[[buildingid_field, 'Max_Depth']]
                    raster_stats_dataframe.fillna(0, inplace=True)
                    raster_stats_table = raster_stats_dataframe.groupby(str(buildingid_field)).agg(
                        Max_Depth=('Max_Depth', 'max'))

                    # Read in building shapefile and fill null values with 0
                    building_file = gpd.read_file(f_path)
                    building_file.fillna(0, inplace=True)

                    # Merge original buildings dataframe with depth table, then export as shapefile
                    buildings_with_depth = building_file.merge(raster_stats_table, on=str(buildingid_field))
                    if not buildings_with_depth.empty:
                        mk_change_directory("Buildings_Inundation")
                        buildings_with_depth.to_file(filename="Building_Inundation.shp")
                        if not os.stat(find_file("Buildings_Inundation", ".shp")).st_size == 0:
                            is_depth_empty = False

                        if not is_depth_empty:
                            # Add building value from tax parcels to building shapefile
                            is_tax_empty = True
                            join_file = gpd.GeoDataFrame.from_file(find_file("tax_file", ".shp"))
                            target_file = gpd.GeoDataFrame.from_file(find_file("Buildings_Inundation", ".shp"))
                            buildings_with_tax = sjoin(join_file, target_file, how='right', op='intersects')
                            buildings_with_tax = buildings_with_tax[['Max_Depth', str(tax_field), str(taxid_field), 'geometry']]
                            agg_bldgs_with_tax = buildings_with_tax.dissolve(by=str(taxid_field), aggfunc='mean')
                            agg_bldgs_with_tax=agg_bldgs_with_tax.rename(columns={'Max_Depth': 'Mean_Depth'})
                            bldgs_depth_tax = sjoin(agg_bldgs_with_tax, target_file, how='right', op='intersects')
                            agg_bldgs_depth_tax = bldgs_depth_tax.groupby(str(buildingid_field)).agg(
                                Mean_Depth = ('Mean_Depth','mean'),
                                BLDGVAL = (str(tax_field), 'sum'))
                            target_file = target_file.merge(agg_bldgs_depth_tax, on=str(buildingid_field))
                            target_file = target_file.rename(columns={'Max_Depth': 'Lost_Value'})
                            for idx, row in target_file.iterrows():
                                if 0 < target_file.loc[idx, 'Mean_Depth'] <= depth_0:
                                    target_file.loc[idx, 'Lost_Value'] = bldg_0 * target_file.loc[idx, 'BLDGVAL']
                                elif depth_0 < target_file.loc[idx, 'Mean_Depth'] <= depth_1:
                                    target_file.loc[idx, 'Lost_Value'] = bldg_1* target_file.loc[idx, 'BLDGVAL']
                                elif depth_1 < target_file.loc[idx, 'Mean_Depth'] <= depth_2:
                                    target_file.loc[idx, 'Lost_Value'] = bldg_2 * target_file.loc[idx, 'BLDGVAL']
                                elif target_file.loc[idx, 'Mean_Depth'] > depth_3:
                                    target_file.loc[idx, 'Lost_Value'] = bldg_3 * target_file.loc[idx, 'BLDGVAL']
                                else:
                                    target_file.loc[idx, 'Lost_Value'] = 0
                            if not target_file.empty:
                                mk_change_directory("Parcel_Inundation")
                                target_file.to_file("Parcel_Inundation.shp")
                                if not os.stat(find_file("Parcel_Inundation", ".shp")).st_size == 0:
                                    is_tax_empty = False

                            if not is_tax_empty:
                                # Add land use to building shapefile
                                join_file = gpd.GeoDataFrame.from_file(find_file("landuse_file", ".shp"))
                                target_file = gpd.GeoDataFrame.from_file(find_file("Parcel_Inundation", ".shp"))
                                buildings_with_tax = sjoin(join_file, target_file, how='right', op='intersects')
                                buildings_with_tax = buildings_with_tax[[str(landuse_field), str(landuseid_field), 'geometry']]
                                agg_bldgs_with_tax= buildings_with_tax.dissolve(by=str(landuseid_field), aggfunc='first')
                                bldgs_depth_tax = sjoin(agg_bldgs_with_tax, target_file, how='right', op='intersects')
                                agg_bldgs_depth_tax=bldgs_depth_tax.groupby(str(buildingid_field)).agg(
                                    USE1=(str(landuse_field), 'first'))
                                target_file = target_file.merge(agg_bldgs_depth_tax, on=str(buildingid_field))
                                target_file = target_file.rename(columns={landuse_field:'Land_Use'})
                                target_file.Land_Use.apply(str)
                                for idx, row in target_file.iterrows():
                                    if target_file.loc[idx, 'Land_Use'] in residential_landuse:
                                        target_file.loc[idx, 'Residential'] = 1
                                    else:
                                        target_file.loc[idx, 'Residential'] = 0
                                target_file=target_file.rename(columns={'Land_Use':landuse_field})

                                if not target_file.empty:
                                    mk_change_directory("Landuse_Inundation")
                                    target_file.to_file("Landuse_Inundation.shp")

                                    # Find bounds of final dataframe
                                    target_file = target_file.to_crs("EPSG:4326")
                                    this_bounds = target_file.total_bounds
                                    x1, y1, x2, y2 = this_bounds[0], this_bounds[1], this_bounds[2], this_bounds[3]
                                    this_extent = [x1, y1, x2, y2]
                                    return_obj["extent"] = this_extent

                                    # Convert all coordinates to EPSG:3857 for openlayers vector layer
                                    target_file = target_file.to_crs("EPSG:3857")
                                    # Export building flooding geojson in EPSG:3857
                                    target_file.to_file(filename=("Landuse_Inundation.geojson"), driver='GeoJSON')
                                    mk_change_directory("Landuse_Inundation")
                                    building_features = []
                                    if not os.stat(find_file("Landuse_Inundation", ".geojson")).st_size == 0:
                                        with fiona.open("Landuse_Inundation.geojson") as data_file:
                                            for data in data_file:
                                                building_features.append(data)
                                            return_obj["building_features"] = building_features  # Return manhole features in geojson format

        return JsonResponse(return_obj)



"""
Ajax controller which finds flood depth over streets
"""
def streets_process(request):
    return_obj = {}

    if request.is_ajax() and request.method == 'POST':
        streetid = request.POST["streetid_field"]

        buffer_val = request.POST["buffer"]
        distance_val = request.POST["distance"]

        file_name = "street_file"
        output_file = "Streets_divided"
        output_file2 = "Streets_buffered"

        # Split streets at set distance interval
        divide_lines(str(streetid), float(distance_val), file_name, output_file)

        # Edit file to include all fields
        output_file_path = find_file(output_file, (output_file + ".shp"))

        this_output = gpd.read_file(output_file_path)
        this_output.fillna(0, inplace=True)

        input_file_path = find_file(file_name, ".shp")
        this_input = gpd.read_file(input_file_path)
        this_input = this_input.drop(columns=['geometry'])
        this_input.fillna(0, inplace=True)

        # Associate input street shapefile fields with divided streets shapefile
        streets_with_info = this_output.merge(this_input, on=streetid)

        # Check if the dataframe is empty and if not export to shapefile
        if not streets_with_info.empty:
            mk_change_directory(output_file)
            streets_with_info.to_file(filename=(output_file + ".shp"), overwrite=True)

            # Buffer divided streets shapefile
            add_buffer(streetid, buffer_val, output_file, output_file2, 'Polygon', 'LineString')
            # Extract max flood depth within each street polygon
            max_int_results = max_intersect(output_file2, "depth_file")
            if not max_int_results['is_dataframe_empty']:
                raster_stats_dataframe = max_int_results['return_dataframe']
                raster_stats_dataframe['Max_Depth'] = raster_stats_dataframe['max']
                raster_stats_dataframe.fillna(0, inplace=True)
                raster_stats_dataframe = raster_stats_dataframe[['Index', 'Max_Depth']]
                streets_divided = gpd.read_file(find_file("Streets_divided", ".shp"))
                streets_divided.fillna(0, inplace=True)
                # Associate flood depth with divided streets shapefile
                streets_with_depth = streets_divided.merge(raster_stats_dataframe, on='Index')
                if not streets_with_depth.empty:
                    # Export street flooding shapefile in original crs
                    # pathname = os.path.expanduser('~/Downloads/')
                    # os.chdir(pathname)
                    # streets_with_depth.to_file(filename=("Streets_Inundation.shp"))

                    mk_change_directory("Streets_Inundation")
                    streets_with_depth.to_file(filename=("Streets_Inundation.shp"))

                    # Find the map extent in EPSG:4326 to zoom to layer extent
                    proj_st_with_depth = streets_with_depth.to_crs("EPSG:4326")
                    if not proj_st_with_depth.empty:
                        this_bounds = proj_st_with_depth.total_bounds
                        x1, y1, x2, y2 = this_bounds[0], this_bounds[1], this_bounds[2], this_bounds[3]
                        this_extent = [x1, y1, x2, y2]
                        return_obj["extent"] = this_extent

                    # Convert all coordinates to EPSG:3857 for openlayers vector layer
                    streets_with_depth = streets_with_depth.to_crs("EPSG:3857")
                    # Export street flooding geojson in EPSG:3857
                    streets_with_depth.to_file(filename=("Streets_Inundation.geojson"), driver='GeoJSON')
                    mk_change_directory("Streets_Inundation")
                    streets_features = []
                    if not os.stat(find_file("Streets_Inundation", ".geojson")).st_size == 0:
                        with fiona.open("Streets_Inundation.geojson") as data_file:
                            for data in data_file:
                                streets_features.append(data)
                            return_obj["streets_features"] = streets_features # Return street features in geojson format

        return JsonResponse(return_obj)


"""
Ajax controller which determines if storm sewer or inlet controlled
"""


def manhole_process(request):
    return_obj = {}

    if request.is_ajax() and request.method == 'POST':

        # Read in input fields
        manhole_depth = request.POST["manhole_depth"]
        manholeid = request.POST["manholeid_field"]
        streetid = request.POST["streetid_field"]
        buffer_val = request.POST["street_buffer"]
        distance_val = request.POST["distance"]
        street_rad = request.POST["street_rad"]
        street_depth = ""

        # Extract max street depth from raster

        # Split streets at set distance interval
        divide_lines(str(streetid), float(distance_val), "mhstreet_file", "mhstreet_divided")

        # Edit file to include all fields
        output_file_path = find_file("mhstreet_divided", ".shp")

        this_output = gpd.read_file(output_file_path)
        this_output.fillna(0, inplace=True)

        input_file_path = find_file("mhstreet_file", ".shp")
        this_input = gpd.read_file(input_file_path)
        this_input = this_input.drop(columns=['geometry'])
        this_input.fillna(0, inplace=True)

        # Associate input street shapefile fields with divided streets shapefile
        streets_with_info = this_output.merge(this_input, on=streetid)

        # Check if the dataframe is empty and if not export to shapefile
        if not streets_with_info.empty:
            mk_change_directory("mhstreet_divided")
            streets_with_info.to_file(filename=("mhstreet_divided.shp"), overwrite=True)

            # If the street radio button is yes extract the depth from the raster and associate with divided streets
            if street_rad == "yes":
                street_depth = request.POST["street_depth"]
                streets_with_depth = streets_with_info
            else:
                street_depth = 'St_Depth'

                # Buffer divided streets shapefile
                add_buffer(streetid, buffer_val, "mhstreet_divided", "mhstreet_buffered", 'Polygon', 'LineString')
                # Extract max flood depth within each street polygon
                max_int_results = max_intersect("mhstreet_buffered", "depth_file")

                if not max_int_results['is_dataframe_empty']:
                    raster_stats_dataframe = max_int_results['return_dataframe']
                    raster_stats_dataframe[street_depth] = raster_stats_dataframe['max']
                    raster_stats_dataframe.fillna(0, inplace=True)
                    raster_stats_dataframe = raster_stats_dataframe[['Index', street_depth]]
                    streets_divided = gpd.read_file(find_file("mhstreet_divided", ".shp"))
                    streets_divided.fillna(0, inplace=True)
                    # Associate flood depth with divided streets shapefile
                    streets_with_depth = streets_divided.merge(raster_stats_dataframe, on='Index')

            # Buffer manholes and extract nearby street depth
            if not streets_with_depth.empty:
                buffer_val = request.POST["buffer"]
                add_buffer(manholeid, buffer_val, "manhole_file", "Manhole_radius", 'Polygon', 'Point')

                mh_inun = find_file("manhole_file", ".shp")
                mh_inun = gpd.GeoDataFrame.from_file(mh_inun)

                if manholeid in streets_with_depth.columns:
                    print(streets_with_depth.columns)
                    streets_with_depth = streets_with_depth.drop(columns=[manholeid])

                shapefile = find_file("Manhole_radius", ".shp")
                target_file = gpd.GeoDataFrame.from_file(shapefile)

                # Spatially join street inundation and manhole inundation files
                manholes_with_streets = sjoin(streets_with_depth, target_file, how='right', op='intersects')
                print(manholes_with_streets.columns)

                print(street_depth)

                # Group by objectid to take the max street depth for each manhole objectid
                agg_manhole_street_depth = manholes_with_streets.groupby(str(manholeid)).agg(
                    St_Depth=(street_depth, 'max'))

                # Merge file with manhole file per objectid
                mh_inun = mh_inun.merge(agg_manhole_street_depth, on=str(manholeid))
                mh_inun = mh_inun.rename(columns={manhole_depth: 'MH_Depth'})

                # Determine control at each manhole
                for idx, row in mh_inun.iterrows():
                    if mh_inun.loc[idx, 'MH_Depth'] == 0 and mh_inun.loc[idx, 'St_Depth'] == 0:
                        mh_inun.loc[idx, 'Control'] = "Not in ROW/Model"
                    elif mh_inun.loc[idx, 'MH_Depth'] <= 0 and mh_inun.loc[idx, 'St_Depth'] < 0.5:
                        mh_inun.loc[idx, 'Control'] = "OK"
                    elif mh_inun.loc[idx, 'MH_Depth'] <= 0 and mh_inun.loc[idx, 'St_Depth'] >= 0.5:
                        mh_inun.loc[idx, 'Control'] = "Inlet Controlled"
                    elif mh_inun.loc[idx, 'MH_Depth'] > 0:
                        mh_inun.loc[idx, 'Control'] = "Storm Sewer Controlled"
                    else:
                        mh_inun.loc[idx, 'Control'] = "Not in ROW/Model"

                if not mh_inun.empty:
                    # Export shapefile with street depth, manhole depth, and control in input file crs
                    mk_change_directory("MH_Street_Inundation")
                    mh_inun.to_file("MH_Street_Inundation.shp")

                    # Find bounds of final dataframe
                    mh_inun = mh_inun.to_crs("EPSG:4326")
                    this_bounds = mh_inun.total_bounds
                    x1, y1, x2, y2 = this_bounds[0], this_bounds[1], this_bounds[2], this_bounds[3]
                    this_extent = [x1, y1, x2, y2]
                    return_obj["extent"] = this_extent

                    # Convert all coordinates to EPSG:3857 for openlayers vector layer
                    mh_inun = mh_inun.to_crs("EPSG:3857")
                    # Export manhole flooding geojson in EPSG:3857
                    mh_inun.to_file(filename=("MH_Street_Inundation.geojson"), driver='GeoJSON')
                    mk_change_directory("MH_Street_Inundation")
                    mh_features = []
                    if not os.stat(find_file("MH_Street_Inundation", ".geojson")).st_size == 0:
                        with fiona.open("MH_Street_Inundation.geojson") as data_file:
                            for data in data_file:
                                mh_features.append(data)
                            return_obj["mh_features"] = mh_features  # Return manhole features in geojson format

        return JsonResponse(return_obj)


"""
Ajax controller which determines if pipes are undersized
"""
def pipe_process(request):
    return_obj = {}

    if request.is_ajax() and request.method == 'POST':

        # Read in input values
        pipeid = request.POST["pipeid_field"]
        flow = request.POST["flow"]
        diameter = request.POST["diameter"]
        slope = request.POST["slope"]
        streetid = request.POST["streetid_field"]
        buffer = float(request.POST["pipe_buffer"])
        distance = float(request.POST["distance"])
        mannings_n = float(request.POST["mannings_n"])
        pipe_rad = request.POST["pipe_rad"]

        street_file = "street2_file"
        split_street_file = "Streets2_divided"
        street_buffered_file = "Streets2_buffered"
        pipe_file = "pipe_file"
        pipe_buffered_file = "Pipes_buffered"

        # Split streets at set distance interval
        divide_lines(str(streetid), float(distance), street_file, split_street_file)

        # Edit file to include all fields
        this_output = gpd.read_file(find_file(split_street_file, ".shp"))
        this_output.fillna(0, inplace=True)

        this_input = gpd.read_file(find_file(street_file, ".shp"))
        this_input = this_input.drop(columns=['geometry'])
        this_input.fillna(0, inplace=True)

        # Add fields from input file to divided streets file
        streets_with_info = this_output.merge(this_input, on=streetid)

        # Check if the dataframe is empty and if not export to shapefile
        if not streets_with_info.empty:
            mk_change_directory(split_street_file)
            streets_with_info.to_file(filename=(split_street_file + ".shp"), overwrite=True)
            street_rad = request.POST["street_rad"]

            # If the street radio button is yes extract the depth from the raster and associate with divided streets
            if street_rad == "no":
                street_flow = request.POST["street_flow"]
            else:
                street_flow = 's_flow'
                street_buffer = request.POST["street_buffer"]
                add_buffer(streetid, street_buffer, split_street_file, street_buffered_file, 'Polygon', 'LineString')
                output_intersect = max_intersect(street_buffered_file, "depth2_file")
                if not output_intersect["is_dataframe_empty"]:
                    raster_stats_dataframe = output_intersect["return_dataframe"]
                    raster_stats_dataframe[street_flow] = raster_stats_dataframe['max']
                    raster_stats_dataframe = raster_stats_dataframe.drop(columns=['max', 'geometry', 'Shape_Leng', 'Shape_Area'])
                    target_file = gpd.read_file(find_file(split_street_file, ".shp"))
                    target_file.fillna(0, inplace=True)
                    if street_flow in target_file.columns:
                        target_file = target_file.drop(columns=[street_flow, 'Shape_Leng', 'Shape_Area'])

                    street_with_flow = target_file.merge(raster_stats_dataframe, on=streetid)
                    split_street_file = "Street_Flow"
                    if not street_with_flow.empty:
                        mk_change_directory(split_street_file)
                        street_with_flow.to_file(filename=split_street_file+".shp")

            # Buffer pipes shapefile
            if not os.stat(find_file(split_street_file, ".shp")).st_size == 0:
                add_buffer(pipeid, buffer, pipe_file, pipe_buffered_file, 'Polygon', 'LineString')

                # Spatially join street flow and buffered pipe flow
                f_path = find_file(split_street_file, ".shp")
                left_file = gpd.GeoDataFrame.from_file(f_path)
                left_file = left_file.rename(columns={streetid: 'STREETID'})

                f_path = find_file(pipe_buffered_file, ".shp")
                buffer_file = gpd.GeoDataFrame.from_file(f_path)
                buffer_file = buffer_file.drop(columns=['geometry'])

                # Edit file to include all fields
                this_input = gpd.read_file(find_file(pipe_file, ".shp"))
                this_input.fillna(0, inplace=True)

                right_file = this_input.merge(buffer_file, on=pipeid)
                right_file = right_file.rename(columns={pipeid: 'PIPEID'})

                streets_and_pipes = sjoin(left_file, right_file, how='right', op='intersects')
                streets_and_pipes.fillna(0, inplace=True)
                streets_and_pipes = streets_and_pipes.drop(columns=['index_left'])

                agg_streets_and_pipes = streets_and_pipes.dissolve(by='PIPEID', aggfunc='max')

                # Calculate the pipe diameter necessary to meet flood flows
                for i, j in agg_streets_and_pipes.iterrows():
                    this_diameter = float(agg_streets_and_pipes.loc[i, diameter])
                    this_slope = float(agg_streets_and_pipes.loc[i, slope])
                    agg_streets_and_pipes.loc[i, 'Design_Q'] = (1.486 / mannings_n) * math.pi * math.pow(this_diameter, 2) * 0.25 * math.pow(
                        this_diameter * 0.25, 2 / 3) * math.pow(this_slope, 0.5)

                if street_flow in agg_streets_and_pipes.columns:
                    if pipe_rad == "yes":
                        agg_streets_and_pipes['Q_req'] = (agg_streets_and_pipes[flow] + agg_streets_and_pipes[street_flow]) - agg_streets_and_pipes['Design_Q']
                    else:
                        agg_streets_and_pipes['Q_req'] = (agg_streets_and_pipes[street_flow]) - agg_streets_and_pipes['Design_Q']

                    diameter_options = [0.010417, 0.020833, 0.03125, 0.041667, 0.0625, 0.083333, 0.104167, 0.125,
                                        0.166667, 0.208333, 0.25, 0.291667, 0.333333, 0.375, 0.416667, 0.5, 0.583333,
                                        0.666667, 0.75, 0.833333, 0.916667, 1, 1.166667, 1.333333, 1.5, 1.66667,
                                        1.833333, 2, 2.166667, 2.333333, 2.5, 2.666667, 2.833333, 3, 3.166667, 3.333333,
                                        3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 9, 10, 12]

                    for i, j in agg_streets_and_pipes.iterrows():
                        if agg_streets_and_pipes.loc[i, 'Q_req'] < 0:
                            agg_streets_and_pipes.loc[i, 'Dia_req'] = ''
                            agg_streets_and_pipes.loc[i, 'Dia_sugg'] = agg_streets_and_pipes.loc[i, diameter]
                        else:
                            this_slope = agg_streets_and_pipes.loc[i, slope]
                            q_req = agg_streets_and_pipes.loc[i, 'Q_req'] + agg_streets_and_pipes.loc[i, 'Design_Q']
                            agg_streets_and_pipes.loc[i, 'Dia_req'] = (math.pow(
                                q_req * (mannings_n / 1.486) * (math.pow(4, 5 / 3) / math.pi) * (
                                            1 / math.pow(this_slope, 1 / 2)), 3 / 8))
                            if agg_streets_and_pipes.loc[i, 'Dia_req'] > 12:
                                new_diameter = agg_streets_and_pipes.loc[i, 'Dia_req']
                            else:
                                absolute_difference_function = lambda list_value: abs(list_value-agg_streets_and_pipes.loc[i, 'Dia_req'])
                                new_diameter = min(diameter_options, key=absolute_difference_function)
                                if new_diameter < agg_streets_and_pipes.loc[i, 'Dia_req']:
                                    new_diameter = diameter_options[(diameter_options.index(new_diameter)+1)]
                            agg_streets_and_pipes.loc[i, 'Dia_sugg'] = new_diameter
    
                    # Check if the dataframe is empty and if not export to shapefile
                    if not agg_streets_and_pipes.empty:
                        mk_change_directory("Pipe_Inundation")
                        agg_streets_and_pipes.to_file(filename=("Pipe_Inundation.shp"), overwrite=True)

                        # Find the map extent in EPSG:4326 to zoom to layer extent
                        proj_st_with_pipes = agg_streets_and_pipes.to_crs("EPSG:4326")
                        if not proj_st_with_pipes.empty:
                            this_bounds = proj_st_with_pipes.total_bounds
                            x1, y1, x2, y2 = this_bounds[0], this_bounds[1], this_bounds[2], this_bounds[3]
                            this_extent = [x1, y1, x2, y2]
                            return_obj["extent"] = this_extent

                        # Convert all coordinates to EPSG:3857 for openlayers vector layer
                        proj_st_with_pipes = proj_st_with_pipes.to_crs("EPSG:3857")
                        # Export street flooding geojson in EPSG:3857
                        proj_st_with_pipes.to_file(filename=("Pipe_Inundation.geojson"), driver='GeoJSON')
                        mk_change_directory("Pipe_Inundation")
                        pipes_features = []
                        if not os.stat(find_file("Pipe_Inundation", ".geojson")).st_size == 0:
                            with fiona.open("Pipe_Inundation.geojson") as data_file:
                                for data in data_file:
                                    pipes_features.append(data)
                                return_obj["pipes_features"] = pipes_features  # Return pipe features in geojson format

        return JsonResponse(return_obj)
