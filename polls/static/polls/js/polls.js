var $upsert_question_modal = null;

function showHideClosedList() {
	if ($('#id_open_to').val() == 'lst') {
		$('#div_id_closed_list').show();
	} else {
		$('#div_id_closed_list').hide();
	}
}

function fillQuestion(response) {
	const choice_types = ['MC', 'SC', 'ME', 'SE'];
	if (response == null) {
		response = { question_text: '', question_type: 'YN', question_choices: '' };
	}
	$upsert_question_modal.find('#id_question_text').val(response.question_text);
	question_type = $upsert_question_modal.find('#id_question_type')
	question_type.val(response.question_type);
	question_type.change(function() {
		if (choice_types.includes($(this).val())) {
			$upsert_question_modal.find('#div_id_possible_choices').show();
			$upsert_question_modal.find('#id_possible_choices').change(enableMCSave);
			enableMCSave();
		} else {
			$upsert_question_modal.find('#div_id_possible_choices').hide();
			$upsert_question_modal.find('.modal-card-foot button[type="submit"]').prop('disabled', false);
		}
	})
	if (choice_types.includes(response.question_type)) {
		$upsert_question_modal.find('#id_possible_choices').val(response.possible_choices);
		$upsert_question_modal.find('#id_possible_choices').on('keyup', enableMCSave);
		enableMCSave();
		$upsert_question_modal.find('#div_id_possible_choices').show();
	} else {
		$upsert_question_modal.find('#div_id_possible_choices').hide();
	}
}

function enableMCSave() {
	possible_choices = $upsert_question_modal.find('#id_possible_choices').val();
	possible_choices = possible_choices.trim().split('\n');
	$submit_button = $upsert_question_modal.find('.modal-card-foot button[type="submit"]');
	if (possible_choices.length > 1) {
		$submit_button.prop('disabled', false);
	} else {
		$submit_button.prop('disabled', true);
	}
}

$(document).ready(function() {
	$upsert_question_modal = $('#upsert-question-modal');
	showHideClosedList();
	$('#id_open_to').change(function() {
		showHideClosedList();
	});
})
