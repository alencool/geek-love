
// function submitForm(event, data) {
//     // Create a jQuery object from the form
//     $form = $(event.target);
    
//     // Serialize the form data
//     var formData = $form.serialize();
    
//     $.ajax({
//         url: 'submit.php',
//         type: 'POST',
//         data: formData,
//         cache: false,
//         dataType: 'json',
//         success: function(data, textStatus, jqXHR)
//         {

//         }
//     });
// }

// Connect all the components events
function setUp() {
    
    /////////////////////// VISUAL ///////////////////////

    function layout(){
        $('.isotope').isotope({
            itemSelector: '.columns',
            transitionDuration: 0,
            masonry: {
            columnWidth: '.columns'
            }
        })

    }

    // custom scrollbar for main body
    $('body >div').mCustomScrollbar({
        theme:"minimal",
        scrollButtons:{
          enable:true
        }
    });

    // update scroll content on resize
    $(window).on('resize', function() {
        $("#tab_content").mCustomScrollbar("update");
    });


    $('.modal').on('shown.bs.modal', function (e) {
        $("#tab_content").mCustomScrollbar({
            theme:"minimal-dark",
            updateOnContentResize: false,
        });
    });

    // knobify inputs
    $(".dial").knob();

    // set up nicer looking select for firefox, dam you firefox
    $('.selectpicker').selectpicker();
    

    /////////////////////// SEARCH ///////////////////////

    // set up dynamic search
    $("#search").bind("paste keyup", function() {
        if ($(this).val().length > 0) {
            
            $('#matches').hide();
            $('#results').load($SCRIPT_ROOT + '/search/' + $(this).val(), function() {
                // re-knobify on new content
                $(".dial").knob();
            });
            $('#results').show();
            $(".clearer").show();
            
        } else {
            $('#matches').show();
            $('#results').hide();
            $(".clearer").hide();
        }
    });
    
    // make search clearable
    $(".clearer").hide();
    $(".clearer").click(function () {
        $(this).prev('input').val('').focus();
        $(this).prev('input').keyup();
        $(this).hide();
    });

    /////////////////////// MODAL ///////////////////////
    
    // set up bootstraps tab switching
    $('body').on('click', '#tab a', function(event){
        $(this).tab('show');
        event.preventDefault();
    });
    



    ////////////////////// PROFILES ///////////////////////

    // send a user a message
    $('#profile_modal').on('submit', '#form_send_msg', function(event) {
        console.log('sending a message');
        event.preventDefault(); 
        var formData = $('#form_send_msg').serialize();
        $.ajax({
            url: $SCRIPT_ROOT + '/msg_user',
            type: 'POST',
            data: formData,
            cache: false,
            dataType: 'json',
            success: function(data, textStatus, jqXHR) {
                console.log('sent a message');
            }
        });
        $('#msg').val('');
    });


    ////////////////////// ABOUT ME ///////////////////////


    // for the last input of extendable fields, increment on new text
    $('body').on('keypress', '.extendable', function(event){
        var newInputHtml = '<div class="form-group">' + $(this).parent().parent().html() + '</div>';
        $(this).removeClass('extendable');
        $(this).parent().parent().parent().append(newInputHtml);
        layout();

    });

    // make pressing enter go to the next field
    $('body').on('keydown','.modal input', function (event) {
        // event.preventDefault();
        if (event.keyCode == 13) {
            var next_id = $('input[type=text]').index(this) + 1;
            $('input[type=text]:eq(' + next_id + ')').focus();
        }
    });

    // generates event handler for uploading files
    function uploadFiles(location, sucess_handler) {
        
        var uploader = function (event) {
            console.log('location: ' + location);
            var files = event.target.files;
            var data = new FormData();
            $.each(files, function(key, value) {
                data.append('files', value);
                console.log(value);
            });      
            console.log('uploading files......');
            $.ajax({
                url: location,
                type: 'POST',
                data: data,
                cache: false,
                processData: false,
                contentType: false, 
                success: sucess_handler
            });
        }
        return uploader;
    }

    // handle response of upload photos
    var upload_photos = uploadFiles( $SCRIPT_ROOT + '/upload_photos',
        function (data, textStatus, jqXHR) {
            $('#mePhotos').append(data);
    });

    // handle response of upload profile pic
    var upload_profile_pic = uploadFiles( $SCRIPT_ROOT + '/upload_profile_pic',
        function (data, textStatus, jqXHR) {
            console.log(data);
            $('#meProfilePic').html(data);
            $('#meProfilePic').data('remove', '')

    });

    $('#profile_modal').on('change', '#file_photos', upload_photos);
    $('#profile_modal').on('change', '#file_profile_pic', upload_profile_pic);
    
    
    // Connect up the buttons
    $('#profile_modal').on('click', '#btn_add_profile_pic', function() {
        $('#file_profile_pic').trigger('click');
    });

    $('#profile_modal').on('click', '#btn_remove_profile_pic', function() {
        $('#meProfilePic').load($SCRIPT_ROOT + '/aboutme/load/profile_pic_none');
        $('#meProfilePic').data('remove', 'true')
    });


    $('#profile_modal').on('click', '#btn_add_photos', function() { 
        $('#file_photos').trigger('click');
    });


    function postForm (formSelector, relative_url, handler) {
        var formData = $(formSelector).serialize();
        $.ajax({
            url: $SCRIPT_ROOT + relative_url,
            type: 'POST',
            data: formData,
            cache: false,
            success: handler
        });
    }

    function postData (data, relative_url) {
        $.post($SCRIPT_ROOT + relative_url, data);
    }


    // keep track of all checks
    var no_error;

    function meHeadCheckHandler (data, textStatus, jqXHR) {
        // check response
        no_error = true;
        $("#meHead").html(data.html);
        $('.selectpicker').selectpicker();
        layout();
        if (data.error){
            no_error = false;
        }


        console.log('verified head');
        postForm('#form_meAbout', '/aboutme/check/about', meAboutCheckHandler);
    }


    function meAboutCheckHandler (data, textStatus, jqXHR) {
        // check response

        $("#meAbout").html(data.html);
        $('.selectpicker').selectpicker();
        layout();
        if (data.error){
            no_error = false;
            $("#tab a:first").tab('show');
        }


        console.log('verified about');
        postForm('#form_mePreferences', '/aboutme/check/preferences', mePreferencesCheckHandler);
    }

    function mePreferencesCheckHandler (data, textStatus, jqXHR) {
        // check response

        $("#mePreferences").html(data.html);
        var selected = $('#hair_colours').data('selected').split(" ");
        $('#pref_gender').selectpicker({width: '70%'});
        $('#hair_colours').selectpicker({width: '70%'});
        $('#hair_colours').selectpicker('val', selected);
        layout();
        if (data.error){
            if (no_error){
                $("#tab a:last").tab('show');
            }
            no_error = false;
        }

        console.log('verified preferences');
        console.log('no_error: ' + no_error);
    
        // if no errors on the forms then save them
        if (no_error) {
            postForm('#form_meHead', '/aboutme/save/head');
            postForm('#form_meAbout', '/aboutme/save/about');
            postForm('#form_mePreferences', '/aboutme/save/preferences');
            postData({'toremove': $('#mePhotos').data('toremove')}, '/aboutme/save/photos');
            postData({'remove': $('#meProfilePic').data('remove')}, '/aboutme/save/profile_pic');
            $('#brand').click();
            $('#profile_modal').modal('hide');
        }
    }

    $('#profile_modal').on('click', '#btn_save_changes', function() {
        // start verifying forms
        postForm('#form_meHead', '/aboutme/check/head', meHeadCheckHandler);


    });

    //---------------------- photos ----------------------------

    // remove photo from dom and add filename to list to remove
    $('#profile_modal').on('click', '.remove-photo', function() {

        var filename = $(this).data('filename');
        var list = $('#mePhotos').data('toremove');
        if (list) {
            $('#mePhotos').data('toremove', list + ' ' + filename);
        } else {
            $('#mePhotos').data('toremove', filename);
        }
        $(this).parent().parent().remove();
    });




    /////////////////////// CORNER MENU LINK //////////////////////////

    // connect up my about me to modal link
    $('#aboutmelink').on('click', function(event){
        event.preventDefault();
        // load event handler, connect up js here
        $('#profile_modal .modal-content').load($SCRIPT_ROOT + '/aboutme/load/skeleton', function() {

            // on tab shown trigger masonary
            $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
                layout();
            })  

            $("#meProfilePic").load($SCRIPT_ROOT + '/aboutme/load/profile_pic');

            $("#meHead").load($SCRIPT_ROOT + '/aboutme/load/head', function() {
                $('.selectpicker').selectpicker();
            });
            $("#meAbout").load($SCRIPT_ROOT + '/aboutme/load/about', function() {
                $('.selectpicker').selectpicker();
            });

            $("#mePhotos").load($SCRIPT_ROOT + '/aboutme/load/photos');

            $("#mePreferences").load($SCRIPT_ROOT + '/aboutme/load/preferences', function() {
                var selected = $('#hair_colours').data('selected').split(" ");
                $('#pref_gender').selectpicker({width: '70%'});
                $('#hair_colours').selectpicker({width: '70%'});
                $('#hair_colours').selectpicker('val', selected);

            });
            // show modal and switch to first time
            // this is nessasary to get masonary working properly
            $("#profile_modal").modal('show');
            $("#tab a:first").tab('show');
        });
        
    });


    // connect up my settings to modal link
    $('#settingslink').on('click', function(event){
        event.preventDefault();
        // load event handler, connect up js here
        $('#profile_modal .modal-content').load($SCRIPT_ROOT + '/panel/skeleton', function() {

      
            $("#email_panel").load($SCRIPT_ROOT + '/panel/email');
            $("#password_panel").load($SCRIPT_ROOT + '/panel/password');
            $("#status_panel").load($SCRIPT_ROOT + '/panel/status');

            $("#profile_modal").modal('show');
        });
        
    });
    ///////////////////// SETTINGS PANEL BUTTON ///////////////////////


    $('#profile_modal').on('submit', '#formPanelEmail', function(event) {
        event.preventDefault(); 

        var formData = $('#formPanelEmail').serialize();
        $.ajax({
            url: $SCRIPT_ROOT + '/panel/email',
            type: 'POST',
            data: formData,
            cache: false,
            success: function(data, textStatus, jqXHR) {
                $('#email_panel').html(data)
            }
        });
    });


    $('#profile_modal').on('submit', '#formPass', function(event) {
        event.preventDefault(); 
        var data = $('#formPass').serialize();
        
        $.post($SCRIPT_ROOT + '/panel/password', data, function(ndata){
            $('#password_panel').html(ndata)

        });
    });
    $('#profile_modal').on('click', '.btn-account', function() {
        // start verifying forms
        data = {'action': $(this).data('action')}
        $.post($SCRIPT_ROOT + '/panel/status', data, function(ndata){
            $('#status_panel').html(ndata)
            console.log(data)

        });
    });


    $('#profile_modal').on('click', '.btn-account', function() {
        // start verifying forms
        data = {'action': $(this).data('action')}
        if (data.action == 'DELETE_CONFIRM'){
            $.post($SCRIPT_ROOT + '/panel/status', data, function(ndata){
                $('#brand').click();
            }); 
        } else {
            $.post($SCRIPT_ROOT + '/panel/status', data, function(ndata){
                $('#status_panel').html(ndata)
            });
        }

    
    });

    /////////////////////// USER CARDS LINK ///////////////////////////

    
    // connect up card to profile modal link
    $('body').on('click', 'a.profile_link', function(event){
        // load user profile into modal and show
        event.preventDefault();
        var username = $(this).data("username")
        
        $('#profile_modal .modal-content').load($SCRIPT_ROOT + '/profile/' + username, function() {
            

            // on tab shown trigger masonary
            $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
                layout();
            })
            
            // show modal and switch to first time
            // this is nessasary to get masonary working properly
            $("#profile_modal").modal('show');
            $("#tab a:first").tab('show');

            // load photos after profile (delay 1second) 
            setTimeout(function () {
                $('#photos').load($SCRIPT_ROOT + '/photos/' + username);

            }, 900);
            
        });
        
    });

    ////////////////////// OVERLAYS ///////////////////////

    // connect up hover overlays
    $('body').on('mouseenter','.overlay-parent',
        function(){
            $(this).find('.top-overlay').fadeIn(250);
            $(this).find('.bottom-overlay').fadeIn(250);
        }
    );
    $('body').on('mouseleave','.overlay-parent',
        function(){
            $(this).find('.top-overlay').fadeOut(10);
            $(this).find('.bottom-overlay').fadeOut(10);
        }
    ); 

    ////////////////////// MESSAGE ///////////////////////

    // if we are to msg a user launch the profile modal
    if ($("#msg_username").length){
        // focus on the textarea only once
        $('#profile_modal').one('shown.bs.modal', function (e) {
            $("#msg").focus();
        });
        $('#msg_username')[0].click();

    }
   
}

$(function() {
    setUp();
});

