$(document).ready ->

  play_button = (button) ->
    button.attr("data-mode", "activate")
    button.addClass("btn-success")
    button.removeClass("btn-warning")
    pp_icon = button.find("i")
    pp_icon.addClass("fa-play")
    pp_icon.removeClass("fa-pause")

  pause_button = (button) ->
    button.attr("data-mode", "temporary_disable")
    pp_icon = button.find("i")
    pp_icon.addClass("fa-pause")
    pp_icon.removeClass("fa-play")
    button.addClass("btn-warning")
    button.removeClass("btn-success")

  $("input[name='enabled']").bootstrapSwitch onSwitchChange: (event, state) ->
    fields = $(this).closest(".form-inline").find("input.ui-timepicker-input")
    play_pause = $(this).closest(".form-inline").find("a.btn")
    if (state)
      play_pause.removeClass("disabled")
      fields.prop("disabled", false)
    else
      play_button(play_pause)
      play_pause.addClass("disabled")
      fields.prop("disabled", true)

  $("input[name='push']").bootstrapSwitch()
  $("input[name='email']").bootstrapSwitch()
  $("input[name='notify_plants']").bootstrapSwitch()
  $("input[name='notify_maintenance']").bootstrapSwitch()

  $("input.ui-timepicker-input").timepicker({ 'timeFormat': 'h:i A', 'forceRoundTime': true })

  namespace = "/settings"
  socket = io.connect('http://' + document.domain + ':' + location.port + namespace)
  socket.on 'control-updated', (resp) ->
    elem = $("#toggle_control_" + resp["control_id"])
    if resp["status"] == "activate"
      pause_button(elem)
    else
      play_button(elem)
  $("a[data-action='update-control']").click ->
    control_id = $(this).closest(".form-inline").find("input[name='id']").val()
    socket.emit('update-control', control_id, $(this).attr("data-mode"))
