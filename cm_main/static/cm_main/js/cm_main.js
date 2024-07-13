$(document).ready(function() {

  // "navbar-burger" management
  $('.navbar-burger').on('click', function(el) {
      // Get the target from the "data-target" attribute
      const target = $(this).data('target');
      const $target = $('#'+target); // this is the navbar-menu
      // Toggle the "is-active" class on both the "navbar-burger" and the "navbar-menu"
      $(this).toggleClass('is-active');
      $target.toggleClass('is-active');
    });

  // alias is-error to is-danger
  $('.is-error').addClass('is-danger');

  // add is-loading class on upload buttons when they are triggered
  $('.upload-button').on('click', function(el) { 
    $(this).addClass('is-loading'); 
  });

  // close notification box on delete
  $('.notification .delete').on('click', function(el) {
    $(this).parent().remove()
  });

  // Add a click event on buttons to open a specific modal
  $('.js-modal-trigger').each(function(index) {
    const modal = $(this).data('target');
    const $target = $('#'+modal);
    // console.log('adding openmodal to '+$target+' modal='+modal)
    $(this).on('click', () => {
      openModal($target);
    });
  });

  // Add a click event on various child elements to close the parent modal
  $('.modal-background, .modal-close, .modal-card-head .delete, .modal-card-foot .button').
    not('.keep-open-on-click').
    on('click', function(el) {
      const $target = $(this).closest('.modal');
      closeModal($target);
    });

  // Add a keyboard event to close all modals
  $(document).on('keydown', (event) => {
    if(event.key === "Escape") {
      closeAllModals();
    }
  });

});

// Functions to open and close a modal
function openModal($el) {
  $el.addClass('is-active');
}

function closeModal($el) {
  $el.removeClass('is-active');
}

function closeAllModals() {
  $('.modal').removeClass('is-active');
}

// function to set a form to make an AJAX call
function ajax_form_action(id, action, on_success, on_error=on_ajax_error) {
  $(id).submit(function () {
    // create an AJAX call
    $.ajax({
      data: $(this).serialize(), // get the form data
      type: $(this).attr('method'), // GET or POST
      url: action,
      success: on_success,
      error: on_error
    });
    return false;
  });
}

// function to execute an action (POST) through ajax with no form
function ajax_action(action, on_success, on_error=on_ajax_error) {
  $.ajax({
    data: {}, // no data
    type: 'POST',
    url: action,
    success: on_success,
    error: on_error
  });
  return false;
}

// function to add a new option to a select
function add_selected_option(id, value, text, message) {
  if (message) add_success_message(message);
  // add option with new value/text
  $(id).append($('<option>').val(value).text(text));
  // and select it
  $(id+' option[value='+value+']').attr('selected','selected');
}

// function to change an option of a select
function change_option(id, value, text, message) {
  if (message) add_success_message(message);
  $(id+' option[value='+value+']').text(text);
}

// function to display messages 
function add_message(kind, message) {
  // add the message
  $(".messages").append('\n\
  <li class="message is-'+kind+'">\
    <div class="message-header">\
      <p>Success</p>\
      <button class="delete" aria-label="delete"></button>\
    </div>\
    <div class="message-body">' + message + '</div></li>');
}
function add_error_message(message) {
  add_message('error', message);
}
function add_success_message(message) {
  add_message('success', message);
}
function add_info_message(message) {
  add_message('info', message);
}

// function to display ajax errors
function on_ajax_error(response) {
  // alert the error if any error occured
  if (response.responseJSON) { console.log(response.responseJSON.errors); }
  else if (response.responseText) { 
    add_error_message(response.responseText);
  } else console.log(response)
}


// function to add an ajax checker to a field
// if response[response_field] is true, then error triggered
function add_ajax_checker(id, validator_url, response_field, error_message) {
  $('#'+id).keyup(function () {
    // create an AJAX call
    $.ajax({
        data: $(this).serialize(), // get the form data
        url: validator_url,
      // on success
      success: function (response) {
        // alert the error if any error occured
          error_id=id+'_error';
          if (response[response_field] == true) {
              $('#'+id).removeClass('is-success').addClass('is-danger');
              $('#'+id).after('<div class="has-text-danger has-background-danger-light has-text-weight-semibold" id="'+error_id+'">'
                              +error_message+'</div>')
          }
          else {
              $('#'+id).removeClass('is-danger').addClass('is-success');
              $('#'+error_id).remove();
          }
      },
      // on error
      error: function (response) {
          // alert the error if any error occured
          console.log(response.responseJSON.errors)
      }
    });
    return false;
  })
}

// to be used eg as <button onclick="printSection($('.printable')">
function printSection(el) {
  var originalContent = $('body').html();
  var printedContent = $(el).clone();
  
  $('body').empty().html(printedContent);
  window.print();
  $('body').html(originalContent);
}


