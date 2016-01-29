set_popover = (states, elem_id) ->
  # This doesn't appear to guard fully...
  if $('#' + elem_id).length
    $('#' + elem_id).popover()
    $('#' + elem_id).on 'show.bs.popover', ->
      states[elem_id] = true
      return
    $('#' + elem_id).on 'hide.bs.popover', ->
      states[elem_id] = false
      return
    if states[elem_id]
      $('#' + elem_id).popover 'show'
  return

$ ->
  # Why does this feel like a hack?
  slot_id = $('#slot_id').get(0).getAttribute('slot_id')
  states = 
    'Humidity': false
    'pH': false
  $('.dial').knob()
  # set_popover(states, "Humidity");
  # set_popover(states, "pH");
  namespace = '/plants'
  plant_namespace = '/plants/' + slot_id
  plant_socket = io.connect('http://' + document.domain + ':' + location.port + plant_namespace)
  socket = io.connect('http://' + document.domain + ':' + location.port + namespace)
  plant_socket.on 'new-data', (stat) ->
    $('#vitals').html stat['new-page']
    # set_popover(states, "Humidity");
    # set_popover(states, "pH");
    return
  socket.on 'data-update', (msg) ->
    socket.emit 'request-data', slot_id
    return
  return
