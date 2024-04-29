document.addEventListener('DOMContentLoaded', () => {
  // Functions to open and close a modal
  function openModal($el) {
    $el.classList.add('is-active');
  }

  function closeModal($el) {
    $el.classList.remove('is-active');
  }

  function closeAllModals() {
    (document.querySelectorAll('.modal') || []).forEach(($modal) => {
      closeModal($modal);
    });
  }

  // Add a click event on buttons to open a specific modal
  (document.querySelectorAll('.js-modal-trigger') || []).forEach(($trigger) => {
    const modal = $trigger.dataset.target;
    const $target = document.getElementById(modal);
    // console.log('adding openmodal to '+$target+' modal='+modal)
    $trigger.addEventListener('click', () => {
      openModal($target);
    });
  });

  // Add a click event on various child elements to close the parent modal
  (document.querySelectorAll('.modal-background, .modal-close, .modal-card-head .delete, .modal-card-foot .button') || []).forEach(($close) => {
    const $target = $close.closest('.modal');

    $close.addEventListener('click', () => {
      closeModal($target);
    });
  });

  // Add a keyboard event to close all modals
  document.addEventListener('keydown', (event) => {
    if(event.key === "Escape") {
      closeAllModals();
    }
  });

});

// function to set a form to make an AJAX call
function set_modal_form_ajax(id, action, on_success, on_error) {
  $(id).submit(function () {
    // create an AJAX call
    $.ajax({
      data: $(this).serialize(), // get the form data
      type: $(this).attr('method'), // GET or POST
      url: action,
      // on success
      success: on_success,
      // on error
      error: on_error
    });
    return false;
  });
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

// alias is-error to is-danger
$(document).ready(function() {
  $('.is-error').addClass('is-danger');
});

// function to add an jax checker to a field
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
