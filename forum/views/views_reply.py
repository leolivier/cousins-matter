from django.forms import ValidationError
from django.shortcuts import get_object_or_404, render
from django.contrib import messages
from django.http import HttpResponse
from django_htmx.http import HttpResponseClientRefresh, trigger_client_event
from django.utils.translation import gettext as _
from django.contrib.auth.decorators import login_required
from cm_main.utils import (
  check_edit_permission,
)
from forum.views.views_follow import (
  check_followers_on_message,
)
from ..models import Post, Message
from ..forms import MessageForm


@login_required
def add_reply(request, pk):
  replyForm = MessageForm(request.POST)
  if replyForm.is_valid():
    replyForm.instance.post_id = pk
    replyForm.instance.author_id = request.user.id
    reply = replyForm.save()
    check_followers_on_message(request, reply)
    response = render(request, "forum/post_detail.html#forum_reply", {"reply": reply, "edit_reply": False}, status=200)
    return trigger_client_event(response, "updateReplyCount", {"delta": 1})
  else:
    errors = replyForm.errors.as_json()
    messages.error(request, _("Errors: ") + errors)
    return HttpResponseClientRefresh()


@login_required
def edit_reply(request, reply):
  reply = get_object_or_404(Message, pk=reply)
  check_edit_permission(request, reply.author)
  if request.method == "POST":
    form = MessageForm(request.POST, instance=reply)
    if form.is_valid():
      reply = form.save()
      return render(request, "forum/post_detail.html#forum_reply", {"reply": reply}, status=200)
    else:
      errors = form.errors.as_json()
      messages.error(request, _("Errors: ") + errors)
      return HttpResponseClientRefresh()
  else:
    form = MessageForm(instance=reply, auto_id=False)
    form.fields["content"].label = False
    # if edit_reply is not in GET, it's True
    edit_reply = request.GET.get("edit_reply", True)
    # print(request.GET, edit_reply)
    return render(
      request, "forum/post_detail.html#forum_reply", {"reply": reply, "reply_form": form, "edit_reply": edit_reply}
    )


@login_required
def delete_reply(request, reply):
  reply = get_object_or_404(Message, pk=reply)
  check_edit_permission(request, reply.author)
  if Post.objects.filter(first_message=reply).exists():
    raise ValidationError(_("Can't delete the first message of a thread!"))
  reply.delete()
  return trigger_client_event(HttpResponse(status=200), "updateReplyCount", {"delta": -1})
