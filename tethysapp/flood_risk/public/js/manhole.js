/*
Declaring global variables
*/
var buffer; //Buffer around manholes to pull max depth from
var distance; //Road segment length
var manholeid_field; //ID of manhole from input shapefile
var previous_size; //Size of map contained within map div

/*
Function to upload input files without fields to the user workspace
*/
function uploadFileNoFields(file_upload_id, file_name){
    var shapefiles = $(file_upload_id)[0].files;

    //Preparing data to be submitted via AJAX POST request
    var data = new FormData();
    data.append("file_name", file_name);
    for (var i=0; i< shapefiles.length; i++){
        data.append("shapefile", shapefiles[i])
    }

    file_upload_process_no_fields(file_upload_id, data);
};

/*
Helper function
Passes files without fields to the ajax to be uploaded to the user workspace
*/
function file_upload_process_no_fields(file_upload_id, data){
    var file_upload = ajax_update_database_with_file("file-upload-move-files", data); //Submitting the data through the ajax function, see main.js for the helper function.
    file_upload.done(function(return_data){
        if("success" in return_data){
            var file_upload_button = $(file_upload_id);
            var file_upload_button_html = file_upload_button.html();
            file_upload_button.text('File Uploaded');
        };
    });
};

/*
Function to upload input files with fields to the user workspace
*/
function uploadFile(file_upload_id, file_name, filetype, number_fields){

    var shapefiles = $(file_upload_id)[0].files;

    //Preparing data to be submitted via AJAX POST request
    var data = new FormData();
    data.append("file_name", file_name);
    data.append("filetype", filetype);
    for (var i=0; i< shapefiles.length; i++){
        data.append("shapefile", shapefiles[i])
    }
    var field_list=[]
    for (var j=0; j<number_fields; j++){
        var n = file_name.slice(0,(file_name.search("_")));
        field_list[j] = n+'-field-select-'+(j);
    }
    console.log(field_list);

    file_upload_process(data, field_list);
};

/*
Helper function
Passes files with fields to the ajax to be uploaded to the user workspace
*/
function file_upload_process(data, field_list){
    var file_upload = ajax_update_database_with_file("file-upload", data); //Submitting the data through the ajax function, see main.js for the helper function.
    file_upload.done(function(return_data){ //Reset the form once the data is added succesfully
        if("field_names" in return_data){
            var options = return_data.field_names;
            console.log(options);
            console.log(field_list);
            for(var j=0; j < field_list.length; j++){
                console.log(field_list.length);
                var select = document.getElementById(field_list[j]);

                // Clear all existing options first:
                select.innerHTML = "<option value=\"" + "Select Field" + "\">" + "Select Field" + "</option>";

                // Populate list with options:
                for(var i = 0; i < options.length; i++){
                    var opt = options[i];
                    select.innerHTML += "<option value=\"" + opt + "\">" + opt + "</option>";
                }
            };
        };
    });
};

/*
Function which extracts flood depths over manholes from raster
and compares this with street flood depth to determine if manholes
are inlet or storm sewer controlled
*/
process_manhole = function(data) {
    $("#loading-modal").modal('show');

    var data = new FormData();

    // Read in input values
    manholeid_field = document.getElementById("manhole-field-select-0").value;
    data.append("manholeid_field", manholeid_field)

    manhole_depth = document.getElementById("manhole-field-select-1").value;
    data.append("manhole_depth", manhole_depth)

    buffer = document.getElementById("manhole-buffer").value;
    data.append("buffer", buffer);

    street_buffer = document.getElementById("mhstreet-buffer").value;
    data.append("street_buffer", street_buffer);

    streetid_field = document.getElementById("mhstreet-field-select-0").value;
    data.append("streetid_field", streetid_field)

    street_depth = document.getElementById("mhstreet-field-select-1").value;
    data.append("street_depth", street_depth)
    console.log(street_depth)

    distance = document.getElementById("distance-input").value;
    data.append("distance", distance);

    street_rad = document.forms[0].elements.street_radio.value;
    data.append("street_rad", street_rad)

    var street_depth_check;
    var street_buffer_check;
    if(street_rad=="yes"){
        street_buffer_check = 0;
        street_depth_check = check(street_depth, "mhstreet-field-select-1-error");
    } else{
        street_buffer_check = check(street_buffer, "mhstreet-buffer-error");
        street_depth_check = 0;
    }

    // Check for errors in input values
    sum_check = (check(buffer, "manhole-buffer-error")
                +street_buffer_check
                +check(distance, "distance-input-error")
                +street_depth_check
                +check(streetid_field, "mhstreet-field-select-0-error")
                +check(manholeid_field, "manhole-field-select-0-error")
                +check(manhole_depth, "manhole-field-select-1-error"))


    if(sum_check == 0){
        var manhole_risk = ajax_update_database_with_file("manhole-process-ajax",data); //Submitting the data through the ajax function, see main.js for the helper function.
        manhole_risk.done(function(return_data){
            //Show download files button
            document.getElementById("download_button").classList.remove("hideDiv");

            //Show and update map
            ol_map = TETHYS_MAP_VIEW.getMap();
            document.getElementById("manhole_map").classList.remove("hideDiv"); // Show the map
            ol_map.setSize(previous_size); // Resize the map to fit the div
            //Remove existing layers from map
            var layers = ol_map.getLayers();
            layers.forEach(function(layer){
                ol_map.removeLayer(layer);
            });
            ol_map.renderSync(); // Update the map
            (document.getElementsByClassName("collapsible"))[0].click(); // Collapse input menu div

            // Style manhole layer
            var none_style = [
                new ol.style.Style({
                    image: new ol.style.Circle({
                        stroke: new ol.style.Stroke({
                            color: '#A9A9A9',
                            width: 1,
                        }),
                        fill: new ol.style.Fill({
                            color: 'green',
                        }),
                        radius: 5
                    }),
                    stroke: new ol.style.Stroke({
                        color: '#A9A9A9',
                        width: 1,
                    }),
                    fill: new ol.style.Fill({
                        color: 'green',
                    })
                }),
            ];
            var low_style = [
                new ol.style.Style({
                    image: new ol.style.Circle({
                        stroke: new ol.style.Stroke({
                            color: '#A9A9A9',
                            width: 1,
                        }),
                        fill: new ol.style.Fill({
                            color: 'yellow',
                        }),
                        radius: 5
                    }),
                    stroke: new ol.style.Stroke({
                        color: '#A9A9A9',
                        width: 1,
                    }),
                    fill: new ol.style.Fill({
                        color: 'yellow',
                    })
                }),
            ];
            var med_style = [
                new ol.style.Style({
                    image: new ol.style.Circle({
                        stroke: new ol.style.Stroke({
                            color: '#A9A9A9',
                            width: 1,
                        }),
                        fill: new ol.style.Fill({
                            color: 'orange',
                        }),
                        radius: 5
                    }),
                    stroke: new ol.style.Stroke({
                        color: '#A9A9A9',
                        width: 1,
                    }),
                    fill: new ol.style.Fill({
                        color: 'orange',
                    })
                }),
            ];
            var high_style = [
                new ol.style.Style({
                    image: new ol.style.Circle({
                        stroke: new ol.style.Stroke({
                            color: '#A9A9A9',
                            width: 1,
                        }),
                        fill: new ol.style.Fill({
                            color: 'red',
                        }),
                        radius: 5
                    }),
                    stroke: new ol.style.Stroke({
                        color: '#A9A9A9',
                        width: 1,
                    }),
                    fill: new ol.style.Fill({
                        color: 'red',
                    })
                }),
            ];

            // Create a geojson object holding manhole features
            var geojson_object = {
                'type': 'FeatureCollection',
                'crs': {
                    'type': 'name',
                    'properties': {
                        'name': 'EPSG:3857'
                    }
                },
                'features': return_data.mh_features
            };

            // Convert from geojson to openlayers collection
            var these_features = new ol.format.GeoJSON().readFeatures(geojson_object);

            // Divide geojson feature collection by Max_Depth
            var none_features = []
            var low_features = []
            var med_features = []
            var high_features = []
            these_features.forEach(function(feature){
                if (feature.get('Control')=='Inlet Controlled'){
                    med_features.push(feature);
                } else if (feature.get('Control')=='Storm Sewer Controlled'){
                    low_features.push(feature);
                } else {
                    none_features.push(feature);
                }
            });

            // Create a new ol source and assign street features
            var none_vectorSource = new ol.source.Vector({
                features: none_features
            });
            var low_vectorSource = new ol.source.Vector({
                features: low_features
            });
            var med_vectorSource = new ol.source.Vector({
                features: med_features
            });

            // Create a new modifiable layer and assign source and style
            var none_layer = new ol.layer.Vector({
                name: 'No Risk',
                source: none_vectorSource,
                style: none_style,
            });
            var low_layer = new ol.layer.Vector({
                name: 'Low Risk',
                source: low_vectorSource,
                style: low_style,
            });
            var med_layer = new ol.layer.Vector({
                name: 'Medium Risk',
                source: med_vectorSource,
                style: med_style,
            });
            var basemap = new ol.layer.Tile({
                source: new ol.source.OSM(),
            });

            // Add streets layer to map
            ol_map = TETHYS_MAP_VIEW.getMap();
            ol_map.addLayer(basemap);
            ol_map.addLayer(none_layer);
            ol_map.addLayer(low_layer);
            ol_map.addLayer(med_layer);
            ol_map = TETHYS_MAP_VIEW.getMap();

            // Print Control
            var printControl = new ol.control.Print();
            ol_map.addControl(printControl);
            // On print save image file
            printControl.on('printing', function(e){
                $('body').css('opacity',  0.5);
            });
            printControl.on(['print', 'error'], function(e){
                $('body').css('opacity',  1);
                // Print success
                if(e.image){
                    e.canvas.toBlob(function(blob){
                        saveAs(blob, 'map.'+e.imageType.replace('image/', ''));
                    }, e.imageType);
                } else {
                    console.warn('No canvas to export');
                }
            });

            // Define a new legend
            var legend = new ol.control.Legend({
                title: 'Legend',
                margin: 5,
                collapsed: false
            });
            ol_map.addControl(legend);

            legend.addRow({
                title: 'Inlet Controlled',
                typeGeom:'Point',
                style: new ol.style.Style({
                    image: new ol.style.Circle({
                        stroke: new ol.style.Stroke({
                            color: '#A9A9A9',
                            width: 1,
                        }),
                        fill: new ol.style.Fill({
                            color: 'orange',
                        }),
                        radius: 5
                    })
                })
            });
            legend.addRow({
                title: "Storm Sewer Controlled",
                typeGeom:'Point',
                style: new ol.style.Style({
                    image: new ol.style.Circle({
                        stroke: new ol.style.Stroke({
                            color: '#A9A9A9',
                            width: 1,
                        }),
                        fill: new ol.style.Fill({
                            color: 'yellow',
                        }),
                        radius: 5
                    })
                })
            });
            legend.addRow({
                title: "Not in ROW/Model",
                typeGeom:'Point',
                style: new ol.style.Style({
                    image: new ol.style.Circle({
                        stroke: new ol.style.Stroke({
                            color: '#A9A9A9',
                            width: 1,
                        }),
                        fill: new ol.style.Fill({
                            color: 'green',
                        }),
                        radius: 5
                    })
                })
            });

//            var scaleLineControl = new ol.control.CanvasScaleLine();
//            ol_map.addControl(scaleLineControl);

            // Add selection interaction
            select = new ol.interaction.Select();
            ol_map.addInteraction(select);

            // Add a popup overlay to the map
            var element = document.getElementById('popup');
            var popup = new ol.Overlay({
                element: element,
                positioning: 'bottom-center',
                stopEvent: false,
                offset:[0,-10],
            });
            ol_map.addOverlay(popup);
            ol_map.on('click', function(event){
                try{
                    var feature = ol_map.getFeaturesAtPixel(event.pixel)[0];
                } catch(err){}
                if(feature){
                    $(element).popover('destroy');
                    setTimeout(function(){
                        var coordinate = feature.getGeometry().getCoordinates();
                        popup.setPosition(coordinate);
                        popupContent = '<div class="manhole-popup">'+
                        '<p>Manhole ID: '+feature.get(manholeid_field)+'</p>'+
                        '<p>Manhole Depth: '+feature.get('MH_Depth')+'</p>'+
                        '<p>Control: '+feature.get('Control')+'</p>'
                        + '</div>';
                        $(element).popover({
                            container: element.parentElement,
                            html: true,
                            sanitize: false,
                            content: popupContent,
                            placement: 'top'
                        });
                        $(element).popover('show');
                    },500);
                } else {
                    $(element).popover('destroy');
                }
            })
            TETHYS_MAP_VIEW.zoomToExtent(return_data.extent) // Zoom to layer
            $("#loading-modal").modal('hide');
        });
    }
}

/*
Function to Download Streets_Inundation and show popup
*/
function downloadFile(){
    var data = new FormData();
    data.append("file_name", "MH_Street_Inundation");
    var file_download = ajax_update_database_with_file("file-download-ajax",data); //Submitting the data through the ajax function, see main.js for the helper function.
    file_download.done(function(return_data){
        download_path = return_data.file_path;
        document.getElementById("myPopup").innerHTML = "Shapefile downloaded to " + download_path;
        $("#popup-modal").modal('show');
    });
}


/*
Function which hides inputs based on radio button
*/
hide_field = function(id_field){
    x = document.getElementById(id_field);
    x.style.display = "none";
}

/*
Function which shows inputs based on radio button
*/
show_field = function(id_field){
    x = document.getElementById(id_field);
    x.style.display = "inline-block";
}

/*
Function to check input fields for errors and return 1 if errors are found
*/
function check(value, error_id){
    if(value.trim()==""){
        document.getElementById(error_id).innerHTML = "Field is not defined"
        return 1;
    }
    else if(value.trim() =="Select Field"){
        document.getElementById(error_id).innerHTML = "Field is not defined"
        return 1;
    }
    else{
        document.getElementById(error_id).innerHTML = ""
        return 0;
    }
};


/*
Function to hide input menu div when button is clicked
*/
$(function(data){
    var coll = document.getElementsByClassName("collapsible");
    coll[0].addEventListener("click", function(){
        console.log(coll[0].innerHTML)
        if(coll[0].innerHTML == '<i class="fa fa-toggle-up"></i>'){
            coll[0].innerHTML = '<i class="fa fa-toggle-down"></i>';
            document.getElementById('manhole-menu').classList.add("hideDiv");
        }
        else{
            coll[0].innerHTML = '<i class="fa fa-toggle-up"></i>';
            document.getElementById('manhole-menu').classList.remove("hideDiv");
        }
    });
});

/*
Function to retrieve map, retrieve map size, and hide map on page load
*/
$(function(data) { //wait for the page to load
    console.log("PAGE LOADED")
    ol_map = TETHYS_MAP_VIEW.getMap();
    previous_size = ol_map.getSize(); // Retrieve map size
    document.getElementById("manhole_map").classList.add("hideDiv"); // Hide ol map
});

$("#submit-manhole").click(process_manhole);

$(function(){

    $('#manhole-shp-upload-input').change(function(){
        uploadFile('#manhole-shp-upload-input', 'manhole_file', ".shp", 2);
    });

    $('#mhstreet-shp-upload-input').change(function(){
        uploadFile('#mhstreet-shp-upload-input', 'mhstreet_file', ".shp", 2);
    });

    $('#depth-shp-upload-input').change(function(){
        uploadFileNoFields('#depth-shp-upload-input', 'depth_file');
    });


    if(document.forms[0].elements.street_radio.value == "yes"){
        console.log("yes")
        show_field('mhstreet-depth');
        hide_field('street-depth-raster');
        hide_field('mhstreet-buffer-group');
    }
    $(document.forms[0].elements.street_radio).change(function(){
        if(document.forms[0].elements.street_radio.value == "no"){
            console.log("no")
            hide_field('mhstreet-depth');
            show_field('street-depth-raster');
            show_field('mhstreet-buffer-group');
        } else {
            console.log("yes")
            show_field('mhstreet-depth');
            hide_field('street-depth-raster');
            hide_field('mhstreet-buffer-group');
        };
    });

});


