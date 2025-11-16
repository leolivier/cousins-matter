from django.conf import settings
from django.forms import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic
from django.db import transaction
from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext as _
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.core.exceptions import RequestDataTooBig
from cm_main.utils import PageOutOfBounds, Paginator, assert_request_is_ajax, check_edit_permission
from forum.views.views_follow import check_followers_on_message, check_followers_on_new_post
from ..models import Post, Message
from ..forms import MessageForm, PostForm, CommentForm
from members.models import Member


class PostsListView(LoginRequiredMixin, generic.ListView):
  model = Post

  def get(self, request, page=1):
    posts = (
      Post.objects.select_related("first_message")
      .annotate(num_messages=Count("message"))
      .all()
      .order_by("-first_message__date")
    )
    try:
      page = Paginator.get_page(
        request, object_list=posts, page_num=page, reverse_link="forum:page", default_page_size=settings.DEFAULT_POSTS_PER_PAGE
      )
      return render(request, "forum/post_list.html", {"page": page})
    except PageOutOfBounds as exc:
      return redirect(exc.redirect_to)


class PostDisplayView(LoginRequiredMixin, generic.DetailView):
  model = Post

  def get(self, request, pk, page_num=1):
    post_id = pk
    post = get_object_or_404(Post, pk=post_id)
    replies = Message.objects.filter(post=post_id, first_of_post=None).all()
    try:
      page = Paginator.get_page(
        request,
        object_list=replies,
        page_num=page_num,
        reverse_link="forum:display_page",
        compute_link=lambda page_num: reverse("forum:display_page", args=[post_id, page_num]),
        default_page_size=settings.DEFAULT_POSTS_PER_PAGE,
      )
      return render(
        request,
        "forum/post_detail.html",
        {
          "page": page,
          "nreplies": replies.count(),
          "post": post,
          "comment_form": CommentForm(),
          "reply_form": MessageForm(),
        },
      )
    except PageOutOfBounds as exc:
      return redirect(exc.redirect_to)


class PostCreateView(LoginRequiredMixin, generic.CreateView):
  model = Post

  @csrf_exempt
  def dispatch(self, request, *args, **kwargs):
    try:
      return super().dispatch(request, *args, **kwargs)
    except RequestDataTooBig:
      return HttpResponseBadRequest(_("The size of the message exceeds the authorised limit."))

  def get(self, request):
    post_form = PostForm()
    message_form = MessageForm()
    return render(request, "forum/post_form.html", context={"post_form": post_form, "message_form": message_form})

  def post(self, request):
    post_form = PostForm(request.POST)
    message_form = MessageForm(request.POST)
    post = message = None
    if post_form.is_valid() and message_form.is_valid():
      try:
        author = Member.objects.only("id").get(id=request.user.id)
        message_form.instance.author_id = author.id
        with transaction.atomic():
          message = message_form.save()
          post_form.instance.first_message = message
          post = post_form.save()
          message.post = post
          message.save()
        # send notifications to followers
        check_followers_on_new_post(request, post)
        return redirect("forum:display", post.id)
      except Exception as e:
        if message and message.id:  # message saved, delete it
          message.delete()
        if post and post.id:  # post saved, delete it
          post.delete()
        raise e
    # if the form is invalid, an error message will be displayed
    return render(request, "forum/post_form.html", context={"post_form": post_form, "message_form": message_form})


class PostEditView(LoginRequiredMixin, generic.UpdateView):
  model = Post
  form_class = PostForm

  @csrf_exempt
  def dispatch(self, request, *args, **kwargs):
    try:
      return super().dispatch(request, *args, **kwargs)
    except RequestDataTooBig:
      return HttpResponseBadRequest(_("The size of the message exceeds the authorised limit."))

  def get(self, request, pk):
    instance = get_object_or_404(Post, pk=pk)
    post_form = PostForm(instance=instance)
    message_form = MessageForm(instance=instance.first_message)
    return render(
      request, "forum/post_form.html", context={"post_form": post_form, "message_form": message_form, "post": instance}
    )

  def post(self, request, pk):
    instance = get_object_or_404(Post, pk=pk)
    check_edit_permission(request, instance.first_message.author)
    post_form = PostForm(request.POST, instance=instance)
    message_form = MessageForm(request.POST, instance=instance.first_message)
    if post_form.is_valid() and message_form.is_valid():
      message_form.save()
      post = post_form.save()
      return redirect("forum:display", post.id)
    return render(
      request, "forum/post_form.html", context={"post_form": post_form, "message_form": message_form, "post": instance}
    )


@login_required
def delete_post(request, pk):
  post = get_object_or_404(Post, pk=pk)
  check_edit_permission(request, post.first_message.author)
  post.delete()
  return redirect("forum:list")


@login_required
def add_reply(request, pk):
  replyForm = MessageForm(request.POST)
  replyForm.instance.post_id = pk
  replyForm.instance.author_id = request.user.id
  reply = replyForm.save()
  check_followers_on_message(request, reply)
  return redirect(reverse("forum:display", args=[pk]))


@login_required
def edit_reply(request, reply):
  assert_request_is_ajax(request)
  reply = get_object_or_404(Message, pk=reply)
  check_edit_permission(request, reply.author)
  form = MessageForm(request.POST, instance=reply)
  if form.is_valid():
    replyobj = form.save()
    return JsonResponse({"reply_id": replyobj.id, "reply_str": replyobj.content}, status=200)
  else:
    errors = form.errors.as_json()
    return JsonResponse({"errors": errors}, status=400)


@csrf_exempt
@login_required
def delete_reply(request, reply):
  assert_request_is_ajax(request)
  reply = get_object_or_404(Message, pk=reply)
  check_edit_permission(request, reply.author)
  if Post.objects.filter(first_message=reply).exists():
    raise ValidationError(_("Can't delete the first message of a thread!"))
  id = reply.id
  reply.delete()
  return JsonResponse({"reply_id": id}, status=200)
