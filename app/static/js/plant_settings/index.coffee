$ ->
  $("#addThreshold").click ->
    new_form = $("#new-form").find("li").clone()
    new_form.find("a").click ->
       new_form.remove()
    new_form.appendTo("#form-list")
  $("a[data-role='delete']").click ->
    li = $(this).parent().parent().parent()
    delete_input = li.find("input[name='delete']")
    delete_input.attr(value: true)
    li.hide()
