$( "#reset-filter" ).click( function() {
    $( "#from_date" ).val("");
    $( "#to_date" ).val("");
    $( ".radio-label.active" ).removeClass("active");
    $( "input[type=radio]:checked" ).prop("checked", false);
} );
