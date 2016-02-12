hide_flash = ->
  $('.flash').slideUp()
  return

$(document).ready ->
  if $('.flash').size()
    setTimeout hide_flash, 3000
  return
