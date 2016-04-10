log_executed = false
$ ->
  if not log_executed
    log_executed = true
    zip = () ->
      lengthArray = (arr.length for arr in arguments)
      length = Math.min(lengthArray...)
      for i in [0...length]
        arr[i] for arr in arguments
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
    chart_value = "water"
    plant_socket.on 'ideal-chart-data', (stat) ->
      data = stat['chart-content']
      if ideal_chart
        for ary in zip(ideal_chart.segments, data)
          ary[0].value = ary[1]['value']
        ideal_chart.update()
      else
        ideal_chart = new Chart(ideal_ctx).PolarArea(data, animateRotate: false)
      return
    plant_socket.on 'history-chart-data', (stat) ->
      data = stat['chart-content'][chart_value]
      if history_chart
        history_chart.destroy()
      history_chart = new Chart(history_ctx).Line(data,
        animation: false, pointDot: false)
      return
    socket.on 'data-update', (msg) ->
      socket.emit 'request-chart', slot_id
      return

    $("#history-chart-select").find("button").click ->
      $("#history-chart-select").find(".active").removeClass("active")
      $(this).addClass("active")
      chart_value = $(this).attr("name")
      socket.emit 'request-chart', slot_id

    # Send the initial request for chart data
    socket.emit 'request-chart', slot_id
  return
