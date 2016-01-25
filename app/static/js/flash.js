function hide_flash() {
  $(".alert").slideUp()
}

$(document).ready(function() {
  if ($(".alert").size()) {
    setTimeout(hide_flash, 3000)
  }
})