function set_popover(states, elem_id) {
  // This doesn't appear to guard fully...
  if ($('#' + elem_id).length) {
    $('#' + elem_id).popover();
    $('#' + elem_id).on('show.bs.popover', function() {
      states[elem_id] = true;
    });
    $('#' + elem_id).on('hide.bs.popover', function() {
      states[elem_id] = false;
    });
    if (states[elem_id]) {
      $('#' + elem_id).popover("show");
    }
  }
}

$(function() {
  // Why does this feel like a hack?
  var slot_id = $("#slot_id").get(0).getAttribute("slot_id");
  var states = {"Humidity" : false, "pH" : false};
  $(".dial").knob();
  // set_popover(states, "Humidity");
  // set_popover(states, "pH");
  namespace = "/plants"
  plant_namespace = "/plants/" + slot_id;
  var plant_socket = io.connect('http://' + document.domain + ':' + location.port + plant_namespace);
  var socket = io.connect('http://' + document.domain + ':' + location.port + namespace);
  plant_socket.on("new-data", function(stat) {
    $("#vitals").html(stat["new-page"]);
    // set_popover(states, "Humidity");
    // set_popover(states, "pH");
  });
  socket.on("data-update", function (msg) {
    socket.emit("request-data", slot_id);
  });
});
