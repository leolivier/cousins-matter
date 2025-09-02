// $roomSlug, $member, $userName, $pageNumber, $numPages, $lastPageLink, $roomEditLink
// must be defined before including this js script

function escapeHtml(str){
	return new Option(str).innerHTML;
}

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

function get_message_content($data) {
	txt = escapeHtml($data.message)
	if (txt.startsWith("**") && txt.endsWith("**")) {
		txt = '<b>' + txt.slice(2, -2) + '</b>'
	}
	return txt
}

function append_message_data($data) {
	if ($data.message) {
		$messages = $('#chat-messages')
		div_id = 'message-div-' + $data.msgid
		// WARNING! This code is duplicated in room_detail.html!!!
		if ($data.unformated_date_added != $lastDate) {  // new day, show it
			$lastDate = $data.unformated_date_added
			const [year, month, day] = $lastDate.split('-').map(Number);
			const newDate = new Date(year, month - 1, day);
			const options = { year: 'numeric', month: 'long', day: 'numeric' };
			const formattedDate = newDate.toLocaleDateString(undefined, options);

			$messages.append(
				'<p class="has-text-centered is-size-7 has-text-link mx-auto my-3">' +
					formattedDate +
				'</p>'
			);
		}
		$curUserMsg = ($userName == $data.username) // if the message is from the current user
		$showSender = false
		if ($data.username != $lastSender) {
			$lastSender = $data.username;
			$showSender = !$curUserMsg
		}

		if ($curUserMsg) {
			$msg = '<div class="panel-block is-justify-content-flex-end" id="message-div-' + $data.msgid + '">'
		} else {
			$msg = '<div class="panel-block is-flex-wrap-wrap is-align-items-flex-start" id="message-div-' + $data.msgid + '">' +
							'<p class="has-background-white mx-5 br-2">'
		}
		if ($showSender) {
			$msg += '<span class="has-text-primary has-text-weight-bold mx-5">' + $data.full_username + '</span>' +
							'<a href="' + $data.member_url +'" aria-label="' + gettext('profile') +'" class="my-auto">' +
							'	<span class="icon is-large"><i class="mdi mdi-24px mdi-open-in-new" aria-hidden="true"></i></span>' +
							'</a>' +
							'<br>'
		}
		if ($curUserMsg) {
			$msg += '<span class="content mr-1 my-auto px-2 py-1 has-background-primary-light br-2">'
		} else {
			$msg += '<span class="content has-text-left mx-5 my-auto">'
		}
		$msg += get_message_content($data) + '</span>' +
			'<span class="is-size-7 mx-2 my-auto has-text-right">' + escapeHtml($data.date_added) + '</span>'
		if ($curUserMsg) {
			$msg += '<div class="button delete-chat-message my-auto" title="' + gettext('Delete') + 
							'" data-msgid="' + $data.msgid + '">'
							'		<span class="icon is-large"><i class="mdi mdi-24px mdi-trash-can-outline" aria-hidden="true"></i></span>' +
							'	</div>'
		} else {
			$msg += '</p>'
		}
		$msg += '</div>'

		$messages.append($msg)

		scrollMsgsBottom()
	} else {
		alert(gettext('The message was empty!'))
	}
}

function update_message_data($data) {
	if ($('#message-div-' + $data.msgid).length > 0) {
		txt = get_message_content($data) + " <i> (*)</i>"
		$('#message-div-' + $data.msgid + ' span.content').html(txt)
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
		// console.log($data)
		switch ($data.action) {
			case 'create_chat_message':
				if ($pageNumber == $numPages) {
					append_message_data($data.args)
				} else {
					goto_page_url($lastPageLink)
				}
				break
			case 'update_chat_message':
				update_message_data($data.args)
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
					'msgid': msgid,
				}
			}));
		}
	}

	function onclick_edit_chat_message(e) {
		const msgid = $(this).data('msgid');
		const $block = $('#message-div-' + msgid)
		if ($block.length > 0) {
			content = escapeHtml($block.find('span.content').text())
			$block.append('<input class="input" type="text" id="chat-message-edit" value="' + content + '">')
			// if enter is pressed on the message input, submit the content
			$('#chat-message-edit').on('keyup', (e) => {
				if (e.keyCode === 13) {
					new_content = $('#chat-message-edit').val()
					$chatSocket.send(JSON.stringify({
						'action': 'update_chat_message',
						'args': {
							'msgid': msgid,
							'message': new_content
						}
					}));
					$('#chat-message-edit').remove()
				}
			});
		}
	}

	$('#chat-messages').on('click', '.delete-chat-message', onclick_delete_chat_message)

	$('#chat-messages').on('click', '.edit-chat-message', onclick_edit_chat_message)

	// scroll the messages to the bottom of the page
	scrollMsgsBottom()
});

