
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
    
    // custom scrollbar for main body
    $('body >div').mCustomScrollbar({
        theme:"minimal",
        scrollButtons:{
          enable:true
        }
    });

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


    
    // set up nicer looking select for firefox, dam you firefox
    $('.selectpicker').selectpicker({});
    
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
    
    // set up bootstraps tab switching
    $('body').on('click', '#tab a', function(event){
        $(this).tab('show');
        event.preventDefault();
    });
    



    ////////////////////////new text field///////////////////////

    // for the last input of extendable fields, increment on new text
    $('body').on('keypress', '.extendable', function(event){
        var newInputHtml = '<div class="form-group">' + $(this).parent().parent().html() + '</div>';
        $(this).removeClass('extendable');
        $(this).parent().parent().parent().append(newInputHtml);
        $('.isotope').isotope({
            itemSelector: '.columns',
            transitionDuration: 0,
            masonry: {
            columnWidth: '.columns'
            }
        })

    });

    // make pressing enter go to the next field
    $('body').on('keydown','.modal input', function (event) {
        // event.preventDefault();
        if (event.keyCode == 13) {
            console.log('hey hey ehey')
            var next_id = $('input[type=text]').index(this) + 1;
            $('input[type=text]:eq(' + next_id + ')').focus();
        }
    });


    ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    

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

    // hand response of upload photos
    var upload_photos = uploadFiles( $SCRIPT_ROOT + '/upload_photos',
        function (data, textStatus, jqXHR) {
            alert('uploaded photos');
    });

    // handle response of upload profile pic
    var upload_profile_pic = uploadFiles( $SCRIPT_ROOT + '/upload_profile_pic',
        function (data, textStatus, jqXHR) {
            alert('uploaded profile pic');
    });

    $('#profile_modal').on('change', '#file_photos', upload_photos);
    $('#profile_modal').on('change', '#file_profile_pic', upload_profile_pic);
    $('#profile_modal').on('click', '#btn_add_photos', function() { 
        $('#file_photos').trigger('click');
    });
    $('#profile_modal').on('click', '#btn_add_profile_pic', function() {
        $('#file_profile_pic').trigger('click');
    });


    // connect up my about me to modal link
    $('#aboutmelink').on('click', function(event){
        event.preventDefault();
        // load event handler, connect up js here
        $('#profile_modal .modal-content').load($SCRIPT_ROOT + '/aboutme/load/skeleton', function() {

            // on tab shown trigger masonary
            $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
                
                $('.isotope').isotope({
                    itemSelector: '.columns',
                    transitionDuration: 0,
                    masonry: {
                    columnWidth: '.columns'
                    }
                })
            })  


            $("#meHead").load($SCRIPT_ROOT + '/aboutme/load/head', function() {
                $('.selectpicker').selectpicker();
            });
            $("#meAbout").load($SCRIPT_ROOT + '/aboutme/load/about');
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

    ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

    
    // connect up card to profile modal link
    $('body').on('click', 'a.profile_link', function(event){
        // load user profile into modal and show
        event.preventDefault();
        var username = $(this).data("username")
        
        $('#profile_modal .modal-content').load($SCRIPT_ROOT + '/profile/' + username, function() {
            

            // on tab shown trigger masonary
            $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
                
                $('.isotope').isotope({
                    itemSelector: '.columns',
                    transitionDuration: 0,
                    masonry: {
                    columnWidth: '.columns'
                    }
                })
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

    // connect up hover overlays
    $('body').on('mouseenter','.overlay-parent',
        function(){
            console.log('what up doc');
            $(this).find('.top-overlay').fadeIn(250);
            $(this).find('.bottom-overlay').fadeIn(250);

        }
    );
    $('body').on('mouseleave','.overlay-parent',
        function(){
            console.log('whats down doc');
            $(this).find('.top-overlay').fadeOut(250);
            $(this).find('.bottom-overlay').fadeOut(250);
        }
    ); 

}

$(function() {
    setUp();
});

