// $roomSlug, $member, $userName, $pageNumber, $numPages, $lastPageLink, $roomEditLink
// must be defined before including this js script

// room edit form functions

function hide_edit_room_form(value) {
	if (value) { 
		$('#show-room-name').text(value)
	}
	$('#room-edit-form input:text').val(''); 
	$('#room-edit-form').hide()
	$('#show-room-name').show()
}

function toggle_edit_room_form() {
	content = $('#show-room-name').text()
	$('#room-edit-form input:text').val(content);
	$('#show-room-name, #room-edit-form').toggle()
	$input=$('#room-name-input')
	if ($input.is(':visible')) 
		$input.focus();
	else
	$('#chat-message-input').focus();
}

function delete_room(url) {
	if (confirm(gettext('Are you sure you want to delete this room?'))) {
		window.location.href = url;
	}
}

$(document).ready(()=>{
	// hide the room form
	$('#room-edit-form').hide();
	// bind the edit room button to call room-edit then hide the form on response
	ajax_form_action('#room-edit-form', $roomEditLink, (response)=>{
		hide_edit_room_form(response.room_name)
	})
	// Add a keyboard event to close the room form on escape
	$(document).on('keydown', (event) => {
		if(event.key === "Escape") {
			hide_edit_room_form();
		}
	});
	// if enter is pressed on the room name input, submit the room name form
	$('#room-name-input').on('keyup', (e) => {
		if (e.keyCode === 13) {
			$('#room-name-submit').trigger('click');
		}
	});
});

// chat functions

function scrollMsgsBottom() {
	$messages = $('#chat-messages')
	$messages.scrollTop($messages[0].scrollHeight)
	// focus the message input
	$('#chat-message-input').focus();

}

function append_message_data(e) {
	const $data = JSON.parse(e.data);
	if ($data.message) {
		$messages = $('#chat-messages')
		$messages.append(
			'<div class="panel-block has-text-right">' +
				'<p class="has-text-primary has-text-weight-bold mr-5">' + $data.username + '<br>' +
				'  <span class="is-size-7">' + $data.date_added + '</span></p>' +
				'<p class="content">' + $data.message + '</p>' + 
			'</div>');
			scrollMsgsBottom()
	} else {
		alert(gettext('The message was empty!'))
	}
}

$(document).ready(()=>{

	const $chatSocket = new WebSocket(
		'ws://' + window.location.host + '/chat/' + $roomSlug
	);

	$chatSocket.onclose = (e) => {
		console.error('The socket closed unexpectedly');
	};

	$chatSocket.onmessage = (e) => {
		if ($pageNumber == $numPages) {
			append_message_data(e)
		} else {
			goto_page_url($lastPageLink)
		}
}	;

	$('#chat-message-submit').on('click', (e) => {
		const $msg_el = $('#chat-message-input');
		const $message = $msg_el.val();

		$chatSocket.send(JSON.stringify({
			'message': $message,
			'member': $member,
			'username': $userName,
			'room': $roomSlug,
		}));

		$msg_el.val('');
	});

	// if enter is pressed on the message input, submit the message form
	$('#chat-message-input').on('keyup', (e) => {
		if (e.keyCode === 13) {
			$('#chat-message-submit').trigger('click');
		}
	});

	// scroll the messages to the bottom of the page
	scrollMsgsBottom()
});

