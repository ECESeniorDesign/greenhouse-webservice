update_bar = (data) ->
  $('#' + data['class']).css('width', data['width'] + '%')
  $('#error_' + data['class']).css('width', data['error-width'] + '%')
  if data['within-tolerance']
    $('#indicator_' + data['class']).css('color', '#66CC66')
    $('#indicator_' + data['class']).removeClass('fa-times').addClass('fa-check')
  else
    $('#indicator_' + data['class']).css('color', '#FF0000')
    $('#indicator_' + data['class']).removeClass('fa-check').addClass('fa-times')
  return

update_vitalinfo = (metric, data) ->
  vital = $("#" + metric).find(".vital-right").find('span')
  vital.html(data['value'])
  if data['within-tolerance']
    vital.css('color', '#66CC66')
  else
    vital.css('color', '#FF0000')
  return

$ ->
  # Why does this feel like a hack?
  slot_id = $('#slot_id').get(0).getAttribute('slot_id')
  $('.dial').knob()
  # set_popover(states, "Humidity");
  # set_popover(states, "pH");
  namespace = '/plants'
  plant_namespace = '/plants/' + slot_id
  plant_socket = io.connect('http://' + document.domain + ':' + location.port + plant_namespace)
  socket = io.connect('http://' + document.domain + ':' + location.port + namespace)
  plant_socket.on 'new-data', (data) ->
    update_bar(data['light'])
    update_bar(data['water'])
    update_vitalinfo('acidity', data['acidity'])
    update_vitalinfo('humidity', data['humidity'])
    update_vitalinfo('temperature', data['temperature'])
    return
  socket.on 'data-update', (msg) ->
    socket.emit 'request-data', slot_id
    return
  return
