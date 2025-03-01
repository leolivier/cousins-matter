$(document).ready(function() {
  // Add a click event on buttons to open a specific modal
  $('.js-modal-trigger').each(function(index) {
    const modal = $(this).data('target');
    const $target = $('#'+modal);
    // console.log('adding openmodal to '+$target+' modal='+modal)
    $(this).on('click', (e) => {
      openModal($target);
      e.preventDefault(); // block event even in a form
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

const ObjectIdPlaceholder = '1234567890987654321';  // WARNING: MUST STAY IN SYNC WITH OBJECT_ID_PLACEHOLDER in settings.py!

// function to set a MODAL form to make an AJAX call
function ajax_modal_form_action(form_id, action, on_success, on_error=on_ajax_error, get_url=null, opener_element=null, on_init=null) {
  real_action = action
  real_get_url = get_url
  // assign the action to the form
  $(form_id).submit(function () {
    $.ajax({
      data: $(this).serialize(), // get the form data
      type: $(this).attr('method'), // GET or POST
      url: real_action,
      success: function(response) { 
        window[on_success](response);
      },
      error: on_error
    });
    return false;
  });
  if (!opener_element || !on_init) { return; }
  // add an event to init the modal when the opener (button-s) is/are clicked
  $(opener_element).click(function() {
    // the object_id is used to replace the placeholder in the urls. This is useful for forms that are used for multiple objects
    object_id = $(this).data('id');
    if (object_id) {
      real_action = action.replace(ObjectIdPlaceholder, object_id);
      real_get_url = get_url.replace(ObjectIdPlaceholder, object_id);
    } else {
      real_action = action;
      real_get_url = get_url;
    }
    if (real_get_url) {  // we get the init data from an ajax call before calling on_init
      $.ajax({
        type: 'GET',
        url: real_get_url,
        success: function(response) {
          window[on_init](response);
        },
        error: on_ajax_error
      });
    } else {  // direct call to on_init, no data given, on_init must take the data from the page
      window[on_init]();
    }
  });
}