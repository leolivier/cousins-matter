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

  // Function for opening/closing submenus
  function toggleDropdown($element) {
    $element.addClass('is-active');
    $element.children('.navbar-item.has-dropdown').removeClass('is-active');
    // $element.parents('.navbar-item.has-dropdown').siblings('.navbar-item.has-dropdown').removeClass('is-active');
  }

  // Management of sub-menu opening on mouse-over (desktop only)
  $('.navbar-item.has-dropdown').on('mouseenter', function() {
      if ($(window).width() > 1023) {
          toggleDropdown($(this));
      }
  });

  // Management of sub-menu opening on click (mobile and desktop)
  $('.navbar-item.has-dropdown > .navbar-link').on('click', function(e) {
      e.preventDefault();
      var $dropdown = $(this).closest('.navbar-item.has-dropdown');
      if ($(window).width() > 1023) {
          toggleDropdown($dropdown);
      } else {
          $dropdown.toggleClass('is-active');
          $dropdown.siblings('.navbar-item.has-dropdown').removeClass('is-active');
      }
  });

  // Close submenus on outgoing hover (desktop only)
  $('.navbar-item.has-dropdown').on('mouseleave', function() {
      if ($(window).width() > 1023) {
          $(this).removeClass('is-active');
      }
  });

  // Prevent immediate closure when hovering over sub-menus
  $('.navbar-dropdown').on('mouseenter', function(e) {
      e.stopPropagation();
  });

  // Close submenus when clicked outside
  $(document).on('click', function(e) {
      if (!$(e.target).closest('.navbar-item.has-dropdown').length) {
          $('.navbar-item.has-dropdown').removeClass('is-active');
      }
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

  // close message box on delete
  $('.message .message-header .delete').on('click', function(el) {
    $(this).parent().parent().remove()
  });

// Manage hidden notifications (for admin messages)
  
  // Restore hidden notifications
  const hiddenMessages = JSON.parse(sessionStorage.getItem('hiddenMessages') || '[]');

  hiddenMessages.forEach(id => {
    $(`.admin-message[data-id="${id}"]`).hide();
  });

  // Managing the click on the delete button
  $('.admin-message .delete').click(function() {
    const $message = $(this).closest('.admin-message');
    const messageId = $message.data('id');
    
    $message.hide();
    
    // Save in sessionStorage
    const hidden = JSON.parse(sessionStorage.getItem('hiddenMessages') || '[]');
    hidden.push(messageId);
    sessionStorage.setItem('hiddenMessages', JSON.stringify(hidden));
  });
// End manage hidden notifications

// toggle slider js
  $('.icon-radio-group input[type="radio"]').change(function() {
    var $container = $(this).closest('.toggle-container');
    if ($(this).val() === 'option2') {
        $container.css('--toggle-translate', 'translateX(100%)');
    } else {
        $container.css('--toggle-translate', 'translateX(0)');
    }
    $container.css('--toggle-transition', 'transform 0.3s ease');
    console.log('toggle changed to ' + $(this).val());
  });

  // Set initial state
  checked = $('.icon-radio-group input[type="radio"]:checked');
  $container = checked.closest('.toggle-container');
  $translation = (checked.val() === 'option2') ? 'translateX(100%)' : 'translateX(0)';
  $container.css('--toggle-translate', $translation);
// end toggle slider js
});

// ajax functions

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
function add_ajax_checker(selector, validator_url, response_field, error_message) {
  // console.log(selector, validator_url, response_field, error_message, $(selector));
  const $selector = $(selector);
  $selector.keyup(function () {
    // create an AJAX call
    $.ajax({
        data: $(this).serialize(), // get the form data
        url: validator_url,
      // on success
      success: function (response) {
        const check_error = $selector.next('.ajax-checker-error');
        // pop an alert if any error occured
        if (response[response_field] == true) {
          $selector.removeClass('is-success').addClass('is-danger');
          if (!check_error.length) {
            $selector.after(`
              <div class="has-text-danger has-background-danger-light has-text-weight-semibold ajax-checker-error">
                ${error_message}
              </div>`)
          }
        } else {
          $selector.removeClass('is-danger').addClass('is-success');
          $(check_error).remove();
        }
      },
      error: on_ajax_error
    });
    return false;
  })
}

////// utility functions

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
  option = $(id+' option[value='+value+']');
  option.text(text);
  // and reselect it
  option.attr('selected','selected');
}

// function to display messages 
function add_message(kind, message) {
  // add the message
  $(".message-wrapper").append('\n\
  <li class="message is-'+kind+'">\
    <div class="message-header">\
      <p>Success</p>\
      <button class="delete" aria-label="delete"></button>\
    </div>\
    <div class="message-body">' + message + '</div></li>');
  // close message box on delete
  $('.message .message-header .delete').on('click', function(el) {
    $(this).parent().parent().remove()
  });
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

// function to print only a section of the page
// to be used eg as <button onclick="printSection($('.printable')">
function printSection(el) {
  var originalContent = $('body').html();
  var printedContent = $(el).clone();
  
  $('body').empty().html(printedContent);
  window.print();
  $('body').html(originalContent);
}

function confirm_and_redirect(message, action_url) {
	if (confirm(message)) {
			window.location.replace(action_url);
	}
}
