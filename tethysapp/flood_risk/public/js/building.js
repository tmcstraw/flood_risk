/*
Declaring global variables
*/
var buffer; //Buffer around building outlines to extract depth
var buildingid_field; //Building ID Field
var tax_field; //Parcel value field
var taxid_field; //Parcel ID field
var landuse_field; //Land use field
var landuse_options; //Unique values in land use field

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
Function which extracts flood depths over buildings
and calculates the building value lost and prioritizes
flooding by residential landuse */
process_buildings = function(){
    $("#loading-modal").modal('show');

    var data = new FormData();

    //Read in input fields

    var residential_landuse = []

    data.append("residential_landuse", residential_landuse)

    buffer = document.getElementById("buffer-input").value;
    data.append("buffer", buffer);

    buildingid_field = document.getElementById("bldg-field-select-0").value;
    data.append("buildingid_field", buildingid_field);

    taxid_field = document.getElementById("tax-field-select-0").value;
    data.append("taxid_field", taxid_field);

    tax_field = document.getElementById("tax-field-select-1").value;
    data.append("tax_field", tax_field);

    landuseid_field = document.getElementById("landuse-field-select-0").value;
    data.append("landuseid_field", landuseid_field);

    landuse_field = document.getElementById("landuse-field-select-1").value;
    data.append("landuse_field", landuse_field);

    depth_0 = document.getElementById("depth-value-0").value;
    data.append("depth_0", depth_0);

    depth_1 = document.getElementById("depth-value-1").value;
    data.append("depth_1", depth_1);

    depth_2 = document.getElementById("depth-value-2").value;
    data.append("depth_2", depth_2);

    depth_3 = document.getElementById("depth-value-3").value;
    data.append("depth_3", depth_3);

    bldg_0 = document.getElementById("building-value-0").value;
    data.append("bldg_0", bldg_0)

    bldg_1 = document.getElementById("building-value-1").value;
    data.append("bldg_1", bldg_1)

    bldg_2 = document.getElementById("building-value-2").value;
    data.append("bldg_2", bldg_2)

    bldg_3 = document.getElementById("building-value-3").value;
    data.append("bldg_3", bldg_3)

    //Find errors in input values
    sum_check = (check(buffer, "buffer-input-error")
                +check(buildingid_field, "bldg-field-select-0-error")
                +check(taxid_field, "tax-field-select-0-error")
                +check(tax_field, "tax-field-select-1-error")
                +check(landuseid_field, "landuse-field-select-0-error")
                +check(landuse_field, "landuse-field-select-1-error"))

    if(sum_check==0){
        for (i=0; i<landuse_options.length; i++){
            if(document.getElementById("landuse-"+String(i)).checked==true){
                residential_landuse.push(document.getElementById("landuse-"+String(i)).value)
            }
        }
        var bldg_risk = ajax_update_database_with_file("building-process-ajax",data); //Submitting the data through the ajax function, see main.js for the helper function.
        bldg_risk.done(function(return_data){
            //Show download files button
            document.getElementById("download_button").classList.remove("hideDiv");

            //Show and update map
            ol_map = TETHYS_MAP_VIEW.getMap();
            document.getElementById("building_map").classList.remove("hideDiv"); // Show the map
            ol_map.setSize(previous_size); // Resize the map to fit the div
            //Remove existing layers from map
            var layers = ol_map.getLayers();
            layers.forEach(function(layer){
                ol_map.removeLayer(layer);
            });
            ol_map.renderSync(); // Update the map
            (document.getElementsByClassName("collapsible"))[0].click(); // Collapse input menu div

            // Style building layer
            var none_style = [
                new ol.style.Style({
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
                    stroke: new ol.style.Stroke({
                        color: '#A9A9A9',
                        width: 1,
                    }),
                    fill: new ol.style.Fill({
                        color: 'red',
                    })
                }),
            ];

            // Create a geojson object holding building features
            var geojson_object = {
                'type': 'FeatureCollection',
                'crs': {
                    'type': 'name',
                    'properties': {
                        'name': 'EPSG:3857'
                    }
                },
                'features': return_data.building_features
            };

            // Convert from geojson to openlayers collection
            var these_features = new ol.format.GeoJSON().readFeatures(geojson_object);

            // Divide geojson feature collection by Max_Depth
            var none_features = []
            var low_features = []
            var med_features = []
            var high_features = []
            these_features.forEach(function(feature){
                if (feature.get('Mean_Depth')>1.0){
                    high_features.push(feature);
                } else if (feature.get('Mean_Depth')>0.5){
                    med_features.push(feature);
                } else if (feature.get('Mean_Depth')>(1/3)){
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
            var high_vectorSource = new ol.source.Vector({
                features: high_features
            });

            // Create a new modifiable layer and assign source and style
            var none_streetLayer = new ol.layer.Vector({
                name: 'No Risk',
                source: none_vectorSource,
                style: none_style,
            });
            var low_streetLayer = new ol.layer.Vector({
                name: 'Low Risk',
                source: low_vectorSource,
                style: low_style,
            });
            var med_streetLayer = new ol.layer.Vector({
                name: 'Medium Risk',
                source: med_vectorSource,
                style: med_style,
            });
            var high_streetLayer = new ol.layer.Vector({
                name: 'High Risk',
                source: high_vectorSource,
                style: high_style,
            });
            var basemap = new ol.layer.Tile({
                source: new ol.source.OSM(),
            });

            // Add streets layer to map
            ol_map = TETHYS_MAP_VIEW.getMap();
            ol_map.addLayer(basemap);
            ol_map.addLayer(none_streetLayer);
            ol_map.addLayer(low_streetLayer);
            ol_map.addLayer(med_streetLayer);
            ol_map.addLayer(high_streetLayer);
            ol_map = TETHYS_MAP_VIEW.getMap();

            // Define a new legend
            var legend = new ol.control.Legend({
                title: 'Legend',
                margin: 5,
                collapsed: false
            });
            ol_map.addControl(legend);
            legend.addRow({
                title: 'Depth < 4"',
                typeGeom:'Point',
                style: new ol.style.Style({
                    image: new ol.style.RegularShape({
                        points: 4,
                        radius: 10,
                        angle: Math.PI / 4,
                        stroke: new ol.style.Stroke({ color: '#A9A9A9', width: 1 }),
                        fill: new ol.style.Fill({ color: 'green'})
                    })
                })
            });
            legend.addRow({
                title: '4" < Depth < 6"',
                typeGeom:'Point',
                style: new ol.style.Style({
                    image: new ol.style.RegularShape({
                        points: 4,
                        radius: 10,
                        angle: Math.PI / 4,
                        stroke: new ol.style.Stroke({ color: '#A9A9A9', width: 1 }),
                        fill: new ol.style.Fill({ color: 'yellow'})
                    })
                })
            });
            legend.addRow({
                title: '6" < Depth < 12"',
                typeGeom:'Point',
                style: new ol.style.Style({
                    image: new ol.style.RegularShape({
                        points: 4,
                        radius: 10,
                        angle: Math.PI / 4,
                        stroke: new ol.style.Stroke({ color: '#A9A9A9', width: 1 }),
                        fill: new ol.style.Fill({ color: 'orange'})
                    })
                })
            });
            legend.addRow({
                title: 'Depth > 12"',
                typeGeom:'Point',
                style: new ol.style.Style({
                    image: new ol.style.RegularShape({
                        points: 4,
                        radius: 10,
                        angle: Math.PI / 4,
                        stroke: new ol.style.Stroke({ color: '#A9A9A9', width: 1 }),
                        fill: new ol.style.Fill({ color: 'red'})
                    })
                })
            });

//            var scaleLineControl = new ol.control.CanvasScaleLine();
//            ol_map.addControl(scaleLineControl);

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
                        var coordinate = feature.getGeometry().getLastCoordinate();
                        popup.setPosition(coordinate);
                        popupContent = '<div class="building-popup">'+
                        '<p>Building ID: '+feature.get(buildingid_field)+'</p>'+
                        '<p>Flood Depth: '+feature.get('Mean_Depth')+'</p>' +
                        '<p>Value Lost: '+feature.get('Lost_Value')+'</p>'+
                        '<p>Land Use: '+feature.get(landuse_field)+'</p>'
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
};


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
Function to adjust HTML of following depth row on change
*/
function depthInputs(inputNum){
    if(inputNum < 2){
        console.log("label-depth-value-"+(String(inputNum+1)));
        console.log(document.getElementById("label-depth-value-"+(String(inputNum+1))).innerHTML);
        document.getElementById("label-depth-value-"+(String(inputNum+1))).innerHTML =String(document.getElementById("depth-value-"+String(inputNum)).value);
    }
    else{
        document.getElementById("depth-value-"+(String(inputNum+1))).value = String(document.getElementById("depth-value-"+String(inputNum)).value);
    }

};

/*
Function to populate checkboxes for residential landuse
*/
function residentialLanduse(landuseField, file_name, filetype){
    //Preparing data to be submitted via AJAX POST request
    var data = new FormData();
    data.append("file_name", file_name);
    data.append("filetype", filetype);
    landuse_field = document.getElementById(landuseField).value;
    data.append("landuse_field", landuse_field);

    var residential_landuse = ajax_update_database_with_file("residential-landuse-ajax", data); //Submitting the data through the ajax function, see main.js for the helper function.
    residential_landuse.done(function(return_data){ //Reset the form once the data is added succesfully
        if("residential" in return_data){
            landuse_options = return_data.residential;
            console.log(landuse_options);
            var checkbox = document.getElementById('residential-landuse-checkboxes');

            // Clear all existing options first:
            checkbox.innerHTML = "";

            // Populate list with options:
            for(var i = 0; i < landuse_options.length; i++){
                var opt = landuse_options[i];
                if(i==0){
                    checkbox.innerHTML += "<input type=\"checkbox\" id=\"landuse-"+String(i)+"\" value=\"" + opt + "\">"
                    checkbox.innerHTML += "<label class=\"landuse1\" for=\"landuse-"+String(i)+"\"> " + opt + " </label>"
                } else if (i%3 == 0){
                    checkbox.innerHTML += "<br><input type=\"checkbox\" id=\"landuse-"+String(i)+"\" value=\"" + opt + "\">"
                    checkbox.innerHTML += "<label class=\"landuse1\" for=\"landuse-"+String(i)+"\"> " + opt + " </label>"
                } else {
                    checkbox.innerHTML += "<input type=\"checkbox\" id=\"landuse-"+String(i)+"\" value=\"" + opt + "\">"
                    checkbox.innerHTML += "<label class=\"landuse1\"for=\"landuse-"+String(i)+"\"> " + opt + " </label>"
                }
            }
        };
    });
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
            document.getElementById('building-menu').classList.add("hideDiv");
        }
        else{
            coll[0].innerHTML = '<i class="fa fa-toggle-up"></i>';
            document.getElementById('building-menu').classList.remove("hideDiv");
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
    document.getElementById("building_map").classList.add("hideDiv"); // Hide ol map
});

/*
Function to Download Streets_Inundation and show popup
*/
function downloadFile(){
    var data = new FormData();
    data.append("file_name", "Landuse_Inundation");
    var file_download = ajax_update_database_with_file("file-download-ajax",data); //Submitting the data through the ajax function, see main.js for the helper function.
    file_download.done(function(return_data){
        download_path = return_data.file_path;
        document.getElementById("myPopup").innerHTML = "Shapefile downloaded to " + download_path;
        $("#popup-modal").modal('show');
    });
}

$("#submit-buildings").click(process_buildings);

$(function(){

    $('#bldg-shp-upload-input').change(function(){
        uploadFile('#bldg-shp-upload-input', 'bldg_file', ".shp", 1);
    });

    $('#depth-shp-upload-input').change(function(){
        uploadFileNoFields('#depth-shp-upload-input', 'depth_file');
    });

    $('#tax-shp-upload-input').change(function(){
        uploadFile('#tax-shp-upload-input', 'tax_file', ".shp", 2);
    });

    $('#landuse-shp-upload-input').change(function(){
        uploadFile('#landuse-shp-upload-input', 'landuse_file', ".shp", 2);
    });

    $('#depth-value-0').change(function(){depthInputs(0)});
    $('#depth-value-1').change(function(){depthInputs(1)});
    $('#depth-value-2').change(function(){depthInputs(2)});

    $('#landuse-field-select-1').change(function(){
        residentialLanduse('landuse-field-select-1', 'landuse_file', ".shp")
    });


});


