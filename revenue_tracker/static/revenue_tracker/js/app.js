dateConfig = {
  buttonText: "<i class='glyphicon glyphicon-calendar'></i>",
  changeMonth: true,
  changeYear: true,
  dateFormat: "yy-mm-dd",
  showOn: "button"
};

$( function() {
  $( "input[name='from_date']" ).datepicker(dateConfig);
  $( "input[name='to_date']" ).datepicker(dateConfig);
} );

$( "#reset-filter" ).click( function() {
    $( "#from_date" ).val("");
    $( "#to_date" ).val("");
} );
