$( "#reset-filter" ).click( function() {
    $( "#from_date" ).val("");
    $( "#to_date" ).val("");
    $( ".radio-label.active" ).removeClass("active");
    $( "input[type=radio]:checked" ).prop("checked", false);
} );

$( "#reset-institution-type-filter" ).click( function() {
    $( "#institution-type-filter .radio-label.active" ).removeClass("active");
    $( "#institution-type-filter input[type=radio]:checked" ).prop("checked", false);
} );

$( "#reset-transaction-type-filter" ).click( function() {
    $( "#transaction-type-filter .radio-label.active" ).removeClass("active");
    $( "#transaction-type-filter input[type=radio]:checked" ).prop("checked", false);
} );
