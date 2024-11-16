from django.shortcuts import get_object_or_404, redirect
from django.views import generic
from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.exceptions import RequestDataTooBig
from django.utils.translation import gettext as _

from cousinsmatter.utils import assert_request_is_ajax
from forum.views.views_follow import check_followers_on_comment
from ..models import Message, Comment
from ..forms import CommentForm


class CommentCreateView(LoginRequiredMixin, generic.CreateView):
    model = Comment
    form_class = CommentForm

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except RequestDataTooBig:
            return HttpResponseBadRequest(_("The size of the message exceeds the authorised limit."))

    def post(self, request, message_id):
      message = get_object_or_404(Message, pk=message_id)
      form = CommentForm(request.POST)
      if form.is_valid():
        form.instance.author_id = request.user.id
        form.instance.message_id = message_id
        comment = form.save()
        check_followers_on_comment(request, comment)
        return redirect("forum:display", message.post.id)


class CommentEditView(LoginRequiredMixin, generic.UpdateView):
    model = Comment
    form_class = CommentForm

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except RequestDataTooBig:
            return HttpResponseBadRequest(_("The size of the message exceeds the authorised limit."))

    def post(self, request, pk):
        assert_request_is_ajax(request)
        comment = get_object_or_404(Comment, pk=pk)
        # create a form instance from the request and save it
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            comment = form.save()
            return JsonResponse({"comment_id": comment.id, "comment_str": comment.content}, status=200)
        else:
            errors = form.errors.as_json()
        return JsonResponse({"errors": errors}, status=400)


@csrf_exempt
@login_required
def delete_comment(request, pk):
    assert_request_is_ajax(request)
    comment = get_object_or_404(Comment, pk=pk)
    id = comment.id
    comment.delete()
    return JsonResponse({"comment_id": id}, status=200)
