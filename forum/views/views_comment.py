from django.shortcuts import get_object_or_404, render
from django.views import generic
from django.http import HttpResponseBadRequest, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.exceptions import RequestDataTooBig
from django.utils.translation import gettext as _
from django_htmx.http import HttpResponseClientRefresh
from django.contrib import messages
from django_htmx.http import trigger_client_event
from cm_main.utils import check_edit_permission
from forum.views.views_follow import check_followers_on_comment
from ..models import Message, Comment
from ..forms import CommentForm


class CommentCreateView(LoginRequiredMixin, generic.CreateView):
  model = Comment
  form_class = CommentForm

  def dispatch(self, request, *args, **kwargs):
    try:
      return super().dispatch(request, *args, **kwargs)
    except RequestDataTooBig:
      return HttpResponseBadRequest(_("The size of the message exceeds the authorised limit."))

  def get(self, request, message_id):
    message = get_object_or_404(Message, pk=message_id)
    form = CommentForm()
    return render(request, "forum/comment_list.html#forum_add_comment", {"message": message, "comment_form": form})

  def post(self, request, message_id):
    form = CommentForm(request.POST)
    if form.is_valid():
      form.instance.author_id = request.user.id
      form.instance.message_id = message_id
      comment = form.save()
      check_followers_on_comment(request, comment)
      response = render(request, "forum/comment_list.html#display_comment", {"comment": comment})
      return trigger_client_event(response, "updateCommentCount", {"delta": 1, "message_id": message_id})
    else:
      messages.error(request, form.errors)
      return HttpResponseClientRefresh()


class CommentEditView(LoginRequiredMixin, generic.UpdateView):
  model = Comment
  form_class = CommentForm

  def dispatch(self, request, *args, **kwargs):
    try:
      return super().dispatch(request, *args, **kwargs)
    except RequestDataTooBig:
      return HttpResponseBadRequest(_("The size of the message exceeds the authorised limit."))

  def get(self, request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    form = CommentForm(instance=comment, auto_id=False)
    form.fields["content"].label = False
    # if edit_comment is not in GET, it's True
    edit_comment = request.GET.get("edit_comment", True)
    return render(
      request,
      "forum/comment_list.html#forum_comment",
      {"comment": comment, "comment_form": form, "edit_comment": edit_comment},
    )

  def post(self, request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    check_edit_permission(request, comment.author)
    # create a form instance from the request and save it
    form = CommentForm(request.POST, instance=comment)
    if form.is_valid():
      comment = form.save()
      return render(
        request, "forum/comment_list.html#forum_comment", {"comment": comment, "comment_form": form, "edit_comment": False}
      )
    else:
      errors = form.errors.as_json()
    return JsonResponse({"errors": errors}, status=400)


@login_required
def delete_comment(request, pk):
  comment = get_object_or_404(Comment, pk=pk)
  check_edit_permission(request, comment.author)
  id = comment.id
  comment.delete()
  response = JsonResponse({"comment_id": id}, status=200)
  return trigger_client_event(response, "updateCommentCount", {"delta": -1})
