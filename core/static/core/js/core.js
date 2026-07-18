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
  // check first that the form is valid
  $('.upload-button').on('click', function(el) {
    if ($(this).closest('form')[0].checkValidity()) {
      $(this).addClass('is-loading');
    }
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
  $('.icon-radio-group input[type="radio"][checked="checked"]').each(function() {
    $container = $(this).closest('.toggle-container');
    $translation = ($(this).val() === 'option2') ? 'translateX(100%)' : 'translateX(0)';
    $container.css('--toggle-translate', $translation);
    console.log('toggle initial state: ' + $(this).val());
  });
// end toggle slider js
});

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

// function to print only a section of the page.
// Invoked via the delegated [data-print-section] click handler (see below).
// CSP-safe: detach the live DOM nodes (preserving their jQuery data/listeners),
// print a clone of the target section, then re-attach the originals. This avoids
// $('body').html(originalContent), which would re-parse the HTML and make jQuery
// re-execute every inline <script> via DOMEval — losing the nonce and tripping CSP.
function printSection(el) {
  var $body = $('body');
  var $children = $body.children().detach();
  var section = null;
  try {
    section = document.querySelector(el);
  } catch (e) {
    section = null;
  }
  if (section) {
    $body.append($(section).clone());
  }
  window.print();
  $body.empty().append($children);
}

function check_search_length(el, min_length) {
  if (el.value.length > 0 && el.value.length < min_length) {
    // try to use gettext if available
    var message = (typeof gettext === 'function') ? gettext('Please enter at least ') + min_length + gettext(' characters') : 'Please enter at least ' + min_length + ' characters';
    el.setCustomValidity(message);
    el.reportValidity();
  } else {
    el.setCustomValidity('');
  }
}

// --- CSP-safe replacements for inline on*= handlers (delegated via data-*) ---
// A nonce cannot cover inline event-handler attributes, so they are replaced by
// data-* attributes handled here. Delegation on document keeps them working on
// htmx/AJAX-injected content (pagination, modals).
//   onchange="this.form.submit()"                  → <select data-autosubmit>
//   oninput="check_search_length(this, N)"         → <input data-min-length="N">
//   onclick="goto_page_url(url)"                   → <a data-goto-url="url">
//   onclick="selectMember(id, name); return false" → <a data-select-member-id data-select-member-name>
//   onclick="printSection($(sel))"                 → <button data-print-section="sel">
$(document).on('change', '[data-autosubmit]', function() {
  this.form.submit();
});
$(document).on('input', '[data-min-length]', function() {
  check_search_length(this, Number($(this).attr('data-min-length')));
});
$(document).on('click', '[data-goto-url]', function(e) {
  e.preventDefault();
  goto_page_url($(this).attr('data-goto-url'));
});
$(document).on('click', '[data-select-member-id]', function(e) {
  e.preventDefault();
  selectMember($(this).attr('data-select-member-id'), $(this).attr('data-select-member-name'));
  return false;
});
$(document).on('click', '[data-print-section]', function() {
  printSection($(this).attr('data-print-section'));
});

$(document).on('htmx:load', () => {
	 // Add a click event on various modal child elements to close the parent modal
  $('.modal-background, .modal-close, .modal-card-head .delete, .modal-card-foot .button:not([type="submit"])').
    not('.keep-open-on-click').
    on('click', function(el) {
      $(this).closest('.modal').removeClass('is-active'); // close the parent modal
  });
  $('.confirmation_check').trigger('keyup');
});

$(document).on('keyup', '.confirmation_check', function(event) {
  expected_value = $(this).data('expected-value');
  form=$(this).parents('form');
  submit=form.find('.modal-card-foot button[type="submit"]');
  not_possible = form.find("#deletion_not_possible");
  possible = form.find("#deletion_possible");
  if ( event.target.value == expected_value ) {
    submit.prop('disabled', false);
    possible.removeClass('is-hidden');
    not_possible.addClass('is-hidden');
  } else {
    submit.prop('disabled', true);
    possible.addClass('is-hidden');
    not_possible.removeClass('is-hidden');
  }
});
