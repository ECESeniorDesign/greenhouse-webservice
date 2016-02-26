$(document).ready ->
  $("input[name='enabled']").bootstrapSwitch onSwitchChange: (event, state) ->
    fields = $(this).closest(".form-inline").find("input.ui-timepicker-input")
    play_pause = $(this).closest(".form-inline").find("a.btn")
    if (state)
      play_pause.removeClass("disabled")
      fields.prop("disabled", false)
    else
      play_pause.attr("data-mode", "activate")
      pp_icon = play_pause.find("i")
      pp_icon.addClass("fa-play")
      pp_icon.removeClass("fa-pause")
      play_pause.addClass("disabled btn-success")
      play_pause.removeClass("btn-warning")
      fields.prop("disabled", true)
      
  $("input.ui-timepicker-input").timepicker({ 'timeFormat': 'h:i A', 'forceRoundTime': true })