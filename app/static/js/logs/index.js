$(function() {
  var ideal_ctx = $("#plant_ideal").get(0).getContext("2d");
  var history_ctx = $("#plant_history").get(0).getContext("2d");
  // Why does this feel like a hack?
  var slot_id = $("#slot_id").get(0).getAttribute("slot_id");
  namespace = "/plants"
  plant_namespace = "/plants/" + slot_id;
  var plant_socket = io.connect('http://' + document.domain + ':' + location.port + plant_namespace);
  var socket = io.connect('http://' + document.domain + ':' + location.port + namespace);
  var ideal_chart = null;
  var history_chart = null;
  plant_socket.on("ideal-chart-data", function(stat) {
    var data = stat["chart-content"];
    if (ideal_chart) {
      ideal_chart.destroy();
    }
    ideal_chart = new Chart(ideal_ctx).Pie(data, {animateRotate : false});
  });
  plant_socket.on("history-chart-data", function(stat) {
    var data = stat["chart-content"]
    if (history_chart) {
      history_chart.destroy();
    }
    history_chart = new Chart(history_ctx).Line(data, {
      animation: false,
      scaleOverride: true,
      scaleSteps: 5,
      scaleStepWidth: 20,
      scaleStartValue: 0
      });
  });
  socket.on("data-update", function (msg) {
    socket.emit("request-chart", slot_id);
  });
  // Send the initial request for chart data
  socket.emit("request-chart", slot_id);
});
