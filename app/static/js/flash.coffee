hide_flash = ->
  $('.alert').slideUp()
  return

$(document).ready ->
  if $('.alert').size()
    setTimeout hide_flash, 3000
  return
