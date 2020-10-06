import random
import string
import os

from django.shortcuts import render, reverse
from django import forms
from tethys_sdk.permissions import login_required
from tethys_sdk.gizmos import *
from tethys_sdk.workspaces import user_workspace
from .app import FloodRisk as app
from .ajax_controllers import *
from .utilities import *
import geojson
import fiona
from fiona import transform


@login_required()
def home(request):

    context = {}

    return render(request, 'flood_risk/home.html', context)


@login_required()
def building(request):
    """
    Controller for the Flood Risk Layer Generation Page
    """
    # Define form gizmos

    submit_buildings = Button(
        display_text='Submit',
        name='submit-buildings',
        icon='glyphicon glyphicon-plus',
        style='success',
        attributes={'id': 'submit-buildings'},
    )

    view_options = MVView(
        projection='EPSG:4326',
        center=[-100, 40],
        zoom=3.5,
        maxZoom=18,
        minZoom=2
    )

    drawing_options = []

    # basemaps = ['OpenStreetMap',
    #             'CartoDB',
    #             'Stamen',
    #             'ESRI']

    MapView.old_version = '5.3.0'

    map_view = MapView(
        # height='100%',
        # width='100%',
        # controls=['ZoomSlider', 'Rotate', 'FullScreen',
        #           {'MousePosition': {'projection': 'EPSG:4326'}},
        #           {'ZoomToExtent': {'projection': 'EPSG:4326', 'extent': [-130, 22, -65, 54]}}],
        layers=[],
        view=view_options,
        basemap=None,
        draw=drawing_options
    )

    context = {
        'submit_buildings': submit_buildings,
        'map_view': map_view,
    }

    return render(request, 'flood_risk/building.html', context)

@login_required()
def street(request):
    """
    Controller for the Street Risk Analysis Page
    """

    # layer_crs = 'EPSG:4326'
    # mk_change_directory("Streets_Inundation")
    # if not os.stat(find_file("Streets_Inundation", ".geojson")).st_size == 0:
    #     print("In the if statement")
    #     with fiona.open("Streets_Inundation.geojson") as data_file:
    #         layer_crs = (str(data_file.crs['init'])).upper()
    #         print(layer_crs)
    #
    #         for data in data_file:
    #             # data['geometry'] = transform.transform_geom(src_crs=data_file.crs, dst_crs='EPSG:4326', geom=data['geometry'])
    #             streets_features.append(data)
    #
    #         style = {'ol.style.Style': {
    #             'stroke': {'ol.style.Stroke': {
    #                 'color': 'red',
    #                 'width': 20
    #             }},
    #             'fill': {'ol.style.Fill': {
    #                 'color': 'green'
    #             }},
    #             'image': {'ol.style.Circle': {
    #                 'radius': 10,
    #                 'fill': None,
    #                 'stroke': {'ol.style.Stroke': {
    #                     'color': 'red',
    #                     'width': 2
    #                 }}
    #             }}
    #         }}
    #
    #         geojson_object = {
    #             'type': 'FeatureCollection',
    #             'crs': {
    #                 'type': 'name',
    #                 'properties': {
    #                     'name': "EPSG:4326"
    #                 }
    #             },
    #             'features': streets_features
    #         }
    #
    #         geojson_layer = MVLayer(
    #             source='GeoJSON',
    #             options=geojson_object,
    #             layer_options={'style': style},
    #             legend_title='Test GeoJSON',
    #             legend_extent=[-46.7, -48.5, 74, 59],
    #             legend_classes=[
    #                 MVLegendClass('line', 'Lines', stroke='red')
    #             ],
    #         )

    view_options = MVView(
        projection='EPSG:4326',
        center=[-100, 40],
        zoom=3.5,
        maxZoom=18,
        minZoom=2
    )

    drawing_options = []

    # basemaps=['OpenStreetMap',
    #           'CartoDB',
    #           'Stamen',
    #           'ESRI']

    MapView.old_version = '5.3.0'

    map_view = MapView(
        # height='100%',
        # width='100%',
        # controls=['ZoomSlider', 'Rotate', 'FullScreen',
        #           {'MousePosition': {'projection': 'EPSG:4326'}},
        #           {'ZoomToExtent': {'projection': 'EPSG:4326', 'extent': [-130, 22, -65, 54]}}],
        layers=[],
        view=view_options,
        basemap=None,
        draw=drawing_options
    )

    submit_streets = Button(
        display_text='Submit',
        name='submit-streets',
        icon='glyphicon glyphicon-plus',
        style='success',
        attributes={'id': 'submit-streets'},
    )

    context = {
        'map_view':map_view,
        'submit_streets':submit_streets,
    }

    return render(request, 'flood_risk/street.html', context)

@login_required()
def manhole(request):
    """
    Controller for the Manhole page.
    """

    # Define form gizmos
    submit_manhole = Button(
        display_text='Submit',
        name='submit-manhole',
        icon='glyphicon glyphicon-plus',
        style='success',
        attributes={'id': 'submit-manhole'},
    )
    manhole_buffer = TextInput(
        display_text='',
        name='manhole-buffer',
        placeholder=50,
        attributes={'id': 'manhole-buffer'},
        classes="input buffer-input",
    )

    view_options = MVView(
        projection='EPSG:4326',
        center=[-100, 40],
        zoom=3.5,
        maxZoom=18,
        minZoom=2
    )

    drawing_options = []

    # basemaps = ['OpenStreetMap',
    #             'CartoDB',
    #             'Stamen',
    #             'ESRI']

    MapView.old_version = '5.3.0'

    map_view = MapView(
        # height='100%',
        # width='100%',
        # controls=['ZoomSlider', 'Rotate', 'FullScreen',
        #           {'MousePosition': {'projection': 'EPSG:4326'}},
        #           {'ZoomToExtent': {'projection': 'EPSG:4326', 'extent': [-130, 22, -65, 54]}}],
        layers=[],
        view=view_options,
        basemap=None,
        draw=drawing_options
    )

    context = {
        'manhole_buffer':manhole_buffer,
        'submit_manhole':submit_manhole,
        'map_view':map_view,
    }
    return render(request, 'flood_risk/manhole.html', context)

@login_required()
def pipe(request):
    """
    Controller for the Manhole page.
    """

    # Define form gizmos
    submit_pipe = Button(
        display_text='Submit',
        name='submit-pipe',
        icon='glyphicon glyphicon-plus',
        style='success',
        attributes={'id': 'submit-pipe'},
    )

    map_layers = []

    map_view = MapView(
        height='100%',
        width='100%',
        layers=map_layers,
        controls=[
            'ZoomSlider', 'Rotate', 'FullScreen',
            {'ZoomToExtent':{
                'projection':'EPSG:4326',
                'extent':[29.25, -4.75, 46.25, 5.2]
            }}
        ],
        basemap=None,
        view=MVView(
            projection='EPSG:4326',
            center=[37.880859, 0.219726],
            zoom=7,
            maxZoom=18,
            minZoom=2
        )
    )
    context = {
        'submit_pipe':submit_pipe,
        'map_view':map_view,
    }
    return render(request, 'flood_risk/pipe.html', context)
