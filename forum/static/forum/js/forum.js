function hide_comment_form(sel) {
	$(sel+' input:text').val(''); 
	$(sel).hide()
}
function show_comment_form(sel) {
	$(sel).show()
}
function show_edit_comment_form(id) {
	content = $('#comment-content-'+id).text()
	$('#edit-comment-'+id+' input:text').val(content);
	$('#comment-level-'+id).hide()
	$('#edit-comment-'+id).show()
}
function hide_edit_comment_form(id, value=undefined) {
	if (value) { $('#comment-content-'+id).text(value); }
	$('#edit-comment-'+id+' input:text').val('');
	$('#edit-comment-'+id).hide()
	$('#comment-level-'+id).show()
}
function delete_comment(url, id) {
	if (confirm(gettext("Are you sure you want to delete this comment?"))) {
		ajax_action(url, (response)=>{
			$('#comment-div-'+id).remove()
			update_nb_comments(-1)
		})                
	}
}

function show_edit_reply_form(id) {
	content = $('#reply-content-'+id).html()
	$('#edit-reply-'+id+' div.note-editable').html(content); 
	$('#reply-level-'+id).hide()
	$('#edit-reply-'+id).show()
}
function hide_edit_reply_form(id, value=undefined) {
	if (value) { 
		if (value.includes('<')) {
			$('#reply-content-'+id).html(value);
		} else {
			$('#reply-content-'+id).text(value);
		}
	}
	$('#edit-reply-'+id+' div.note-editable').val('');
	$('#edit-reply-'+id).hide()
	$('#reply-level-'+id).show()
}

function delete_reply(url, id) {
	if (confirm(gettext("Are you sure you want to delete this reply and its comments?"))) {
		ajax_action(url, (response)=>{
			$('#reply-div-'+id).remove()
			update_nb_replies(-1)
		})                
	}
}

function update_nb_replies(delta) {
	nbreplies = $('#nb-replies-id1').text().replace(/[^0-9]/g, '')
	if (nbreplies == '') { nbreplies = delta }
	else { nbreplies = parseInt(nbreplies) + delta }
	formats = ngettext('%s answer', '%s answers', nbreplies)
	nreps = interpolate(formats, [nbreplies])
	$('#nb-replies-id1').text(nreps)
	$('#nb-replies-id2').text(nreps)
}

function update_nb_comments(delta) {
	nbcomments = $('#nb-comments-id').text().replace(/[^0-9]/g, '')
	if (nbcomments == '') { nbcomments = delta }
	else { nbcomments = parseInt(nbcomments) + delta }
	formats = ngettext('%s comment', '%s comments', nbcomments)
	ncoms = interpolate(formats, [nbcomments])
	$('#nb-comments-id').text(ncoms)
}

$(document).ready(()=>{
	$('.comment-form').hide();
	$('.reply-form').hide()
});
