from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic
from django.db import transaction
from django.http import HttpResponseBadRequest, HttpResponseNotFound
from django_htmx.http import HttpResponseClientRedirect
from django.utils.translation import gettext as _
from django.db.models import Count
from django.core.exceptions import RequestDataTooBig
from cm_main.utils import (
  PageOutOfBounds,
  Paginator,
  check_edit_permission,
)
from forum.views.views_follow import (
  check_followers_on_new_post,
)
from ..models import Post, Message
from ..forms import MessageForm, PostForm
from members.models import Member


class PostsListView(generic.ListView):
  model = Post

  def get(self, request, page=1):
    posts = (
      Post.objects.select_related("first_message")
      .annotate(num_messages=Count("message"))
      .all()
      .order_by("-first_message__created")
    )
    try:
      page = Paginator.get_page(
        request,
        object_list=posts,
        page_num=page,
        reverse_link="forum:page",
        default_page_size=settings.DEFAULT_POSTS_PER_PAGE,
      )
      return render(request, "forum/post_list.html", {"page": page})
    except PageOutOfBounds as exc:
      return redirect(exc.redirect_to)


class PostDisplayView(generic.DetailView):
  model = Post

  def get(self, request, pk, page_num=1):
    try:
      post = Post.objects.select_related("first_message").get(pk=pk)
    except Post.DoesNotExist:
      return HttpResponseNotFound()
    replies = Message.objects.filter(post=post, first_of_post=None).all()
    try:
      page = Paginator.get_page(
        request,
        object_list=replies,
        page_num=page_num,
        reverse_link="forum:display_page",
        compute_link=lambda page_num: reverse("forum:display_page", args=[pk, page_num]),
        default_page_size=settings.DEFAULT_POSTS_PER_PAGE,
      )
      return render(
        request,
        "forum/post_detail.html",
        {
          "page": page,
          "nreplies": replies.count(),
          "post": post,
          # "comment_form": CommentForm(),
          # "reply_form": MessageForm(),
        },
      )
    except PageOutOfBounds as exc:
      return redirect(exc.redirect_to)


class PostCreateView(generic.CreateView):
  model = Post

  def dispatch(self, request, *args, **kwargs):
    try:
      return super().dispatch(request, *args, **kwargs)
    except RequestDataTooBig:
      return HttpResponseBadRequest(_("The size of the message exceeds the authorised limit."))

  def get(self, request):
    post_form = PostForm()
    message_form = MessageForm()
    return render(
      request,
      "forum/post_form.html",
      context={"post_form": post_form, "message_form": message_form},
    )

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
    return render(
      request,
      "forum/post_form.html",
      context={"post_form": post_form, "message_form": message_form},
    )


class PostEditView(generic.UpdateView):
  model = Post
  form_class = PostForm

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
      request,
      "forum/post_form.html",
      context={
        "post_form": post_form,
        "message_form": message_form,
        "post": instance,
      },
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
      request,
      "forum/post_form.html",
      context={
        "post_form": post_form,
        "message_form": message_form,
        "post": instance,
      },
    )


def delete_post(request, pk):
  post = get_object_or_404(Post, pk=pk)
  if request.method == "POST":
    check_edit_permission(request, post.first_message.author)
    post.delete()
    return HttpResponseClientRedirect(reverse("forum:list"))
  return render(
    request,
    "cm_main/common/confirm-delete-modal-htmx.html",
    {
      "ays_title": _("Delete post"),
      "ays_msg": _('Are you sure you want to delete "%(post)s" and all associated replies and comments?')
      % {"post": post.title},
      "delete_url": request.get_full_path(),
      "expected_value": post.title,
    },
  )
