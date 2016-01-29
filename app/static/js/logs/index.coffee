$ ->
  ideal_ctx = $('#plant_ideal').get(0).getContext('2d')
  history_ctx = $('#plant_history').get(0).getContext('2d')
  # Why does this feel like a hack?
  slot_id = $('#slot_id').get(0).getAttribute('slot_id')
  namespace = '/plants'
  plant_namespace = '/plants/' + slot_id
  plant_socket = io.connect('http://' + document.domain + ':' + location.port + plant_namespace)
  socket = io.connect('http://' + document.domain + ':' + location.port + namespace)
  ideal_chart = null
  history_chart = null
  plant_socket.on 'ideal-chart-data', (stat) ->
    data = stat['chart-content']
    if ideal_chart
      ideal_chart.destroy()
    ideal_chart = new Chart(ideal_ctx).Pie(data, animateRotate: false)
    return
  plant_socket.on 'history-chart-data', (stat) ->
    data = stat['chart-content']
    if history_chart
      history_chart.destroy()
    history_chart = new Chart(history_ctx).Line(data,
      animation: false
      scaleOverride: true
      scaleSteps: 5
      scaleStepWidth: 20
      scaleStartValue: 0)
    return
  socket.on 'data-update', (msg) ->
    socket.emit 'request-chart', slot_id
    return
  # Send the initial request for chart data
  socket.emit 'request-chart', slot_id
  return
