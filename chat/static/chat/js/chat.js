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

function append_message_data($data) {
	if ($data.message) {
		$messages = $('#chat-messages')
		div_id = 'message-div-' + $data.msgid
		$messages.append(
			'<div class="panel-block has-text-right is-flex is-flex-wrap-wrap is-align-items-flex-start" id="' + div_id + '">' +
			'	<p class="has-text-primary has-text-weight-bold mr-5">' + $data.username +
			'		<a href="' + $data.member_url +'" aria-label="' + gettext('profile') +'">' +
			'			<span class="icon is-large"><i class="mdi mdi-24px mdi-open-in-new" aria-hidden="true"></i></span>' +
			'		</a>' +
			'		<br>' +
			'		<span class="is-size-7">' + $data.date_added + '</span>' +
			'	</p>' +
			'	<p class="content is-flex-grow-1 has-text-left">' + $data.message + '</p>' +
			'	<div class="button is-pulled-right delete-chat-message" title="' + gettext('Delete') + '" data-msgid="' + $data.msgid + '">' +
			'		<span class="icon is-large"><i class="mdi mdi-24px mdi-trash-can-outline" aria-hidden="true"></i></span>' +
			'	</div>' +
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
		const $data = JSON.parse(e.data);
		switch ($data.action) {
			case 'create_chat_message':
				if ($pageNumber == $numPages) {
					append_message_data($data.args)
				} else {
					goto_page_url($lastPageLink)
				}
				break
			case 'delete_chat_message':
				$('#message-div-' + $data.args.msgid).remove()
				break
			default:
				console.error('Unknown action: ' + $data.action)
		}
	};


	$('#chat-message-submit').on('click', (e) => {
		const $msg_el = $('#chat-message-input');
		const $message = $msg_el.val();

		$chatSocket.send(JSON.stringify({
			'action': 'create_chat_message',
			'args': {
				'message': $message,
				'member': $member,
				'username': $userName,
				'room': $roomSlug,
			}
		}));

		$msg_el.val('');
	});

	// if enter is pressed on the message input, submit the message form
	$('#chat-message-input').on('keyup', (e) => {
		if (e.keyCode === 13) {
			$('#chat-message-submit').trigger('click');
		}
	});

	function onclick_delete_chat_message(e) {
		if (confirm(gettext("Are you sure you want to delete this message?"))) {
			const msgid = $(this).data('msgid');
			$chatSocket.send(JSON.stringify({
				'action': 'delete_chat_message',
				'args': {
					'msgid': msgid
				}
			}));
		}
	}

	// $('.delete-chat-message').on('click', onclick_delete_chat_message)
	$('#chat-messages').on('click', '.delete-chat-message', onclick_delete_chat_message)
	// scroll the messages to the bottom of the page
	scrollMsgsBottom()
});

