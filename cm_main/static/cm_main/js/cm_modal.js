$(document).ready(function() {
  // Add a click event on buttons to open a specific modal
  $('.js-modal-trigger').each(function(index) {
    $(this).on('click', (e) => {
      setupAndOpenModal($(this).attr('id'));
      e.preventDefault(); // block event even in a form
    });
  });

  // Add a click event on various child elements to close the parent modal
  $('.modal-background, .modal-close, .modal-card-head .delete, .modal-card-foot .button').
    not('.keep-open-on-click').
    on('click', function(el) {
      $(this).closest('.modal').removeClass('is-active'); // close the parent modal
    });

  // Add a keyboard event to close all modals
  $(document).on('keydown', (event) => {
    if(event.key === "Escape") {
      $('.modal').removeClass('is-active');
    }
  });

});

function init_modal_form(opener_element) {
  get_url = opener_element.data('get-url') || null;
  on_init = opener_element.data('init-function');
  if (get_url) {  // we get the init data from an ajax call before calling on_init
    $.ajax({
      type: 'GET',
      url: get_url,
      success: function(response) {
        window[on_init](response);
      },
      error: on_ajax_error
    });
  } else {  // direct call to on_init, no data given, on_init must take the data from the page
    window[on_init]();
  }
}

function setupAndOpenModal(opener_element_id) {
  opener_element = $('#'+opener_element_id);
  $modal = $(`#${opener_element.data('target')}`);
  form = $modal.find('form');
  action = opener_element.data('action');
  on_success = opener_element.data('onsuccess');
  if (!on_success) {  // don't use ajax
    form.attr('action', action);
  } else {
    // assign the action to the form in ajax
    form.submit(function () {
      $.ajax({
        data: $(this).serialize(), // get the form data
        type: $(this).attr('method'), // GET or POST
        url: action,
        success: function(response) { 
          window[on_success](response);
        },
        error: on_ajax_error
      });
      return false;
    });
  }
  title = opener_element.data('title');
  $modal.find('.modal-card-title').text(title);
  no_warning = opener_element.data('no-warning');
  kind = opener_element.data('kind');
  warning_msg = opener_element.data('warning-msg');
  form.find('.is-warning').hide();
  if (warning_msg) {
    form.find('.is-warning.is-user-warning').text(warning_msg);
    form.find('.is-warning.is-user-warning').show();
  } else if (!no_warning) {
    form.find(`.is-warning.is-${kind}-warning`).show();
  }
  form_fields = opener_element.data('form');
  form.find('.form-placeholder').html(form_fields);
  button = form.find('.modal-card-foot button[type="submit"]');
  button.attr('name', gettext(kind));
  icon = opener_element.data('button-icon');
  if (!icon) {
    switch (kind) {
      case 'create':
        icon = 'plus-circle-outline';
        break;
      case 'update':
        icon = 'check-underline-circle-outline';
        break;
      case 'delete':
        icon = 'trash-can-outline';
        break;
      default:
        icon = 'checkbox-marked-circle-auto-outline';
        break;
    }
  }
  button_text = kind.charAt(0).toUpperCase() + kind.slice(1);  // capitalize
  button.html(`
    <span class="icon">
      <i class="mdi mdi-${icon}"></i>
    </span>
    <span>${gettext(button_text)}</span>`);
  init_modal_form(opener_element);
  above = opener_element.data('above');
  if (above) {
    // make sure $modal is above provided element
    var zIndexBelow = $(above).css('z-index');
    $modal.css('z-index', parseInt(zIndexBelow) + 1);
  }

  $modal.addClass('is-active'); // open modal
}