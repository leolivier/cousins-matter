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
