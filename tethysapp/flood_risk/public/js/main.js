
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


//find if method is csrf safe
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

//add csrf token to appropriate ajax requests
$(function() {
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
            }
        }
    });
}); //document ready


function addErrorMessage(error, div_id) {
    var div_id_string = '#message';
    if (typeof div_id != 'undefined') {
        div_id_string = '#'+div_id;
    }
    $(div_id_string).html(
      '<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>' +
      '<span class="sr-only">Error:</span> ' + error
    )
    .removeClass('hidden')
    .removeClass('alert-success')
    .removeClass('alert-info')
    .removeClass('alert-warning')
    .addClass('alert')
    .addClass('alert-danger');

}
//Add success message when stuff gets done successfully
function addSuccessMessage(message, div_id) {
    var div_id_string = '#message';
    if (typeof div_id != 'undefined') {
        div_id_string = '#'+div_id;
    }
    $(div_id_string).html(
      '<span class="glyphicon glyphicon-ok-circle" aria-hidden="true"></span>' +
      '<span class="sr-only">Sucess:</span> ' + message
    ).removeClass('hidden')
    .removeClass('alert-danger')
    .removeClass('alert-info')
    .removeClass('alert-warning')
    .addClass('alert')
    .addClass('alert-success');
}

//send data to database but follow this if you have files assosciated with it.
function ajax_update_database_with_file(ajax_url, ajax_data,div_id) {
    //backslash at end of url is required
    if (ajax_url.substr(-1) !== "/") {
        ajax_url = ajax_url.concat("/");
    }

    //update database
    var xhr = jQuery.ajax({
        url: ajax_url,
        type: "POST",
        data: ajax_data,
        dataType: "json",
        processData: false, // Don't process the files
        contentType: false // Set content type to false as jQuery will tell the server its a query string request
    });
    xhr.done(function(data) {
        //if("success" in data){
            //addSuccessMessage(data['success'],div_id);
        //}else{
            //appendErrorMessage(data['error'],div_id);
        //}
    })
    .fail(function(xhr, status, error) {

        console.log(xhr.responseText);

    });
    return xhr;
}
