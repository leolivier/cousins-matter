from django.conf import settings
from django.forms import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic
from cousinsmatter.utils import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext as _
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from cousinsmatter.utils import is_ajax
from .models import Post, Message, Comment
from .forms import MessageForm, PostForm, CommentForm
from members.models import Member


class PostsListView(LoginRequiredMixin, generic.ListView):
    model = Post

    def get_context_data(self, **kwargs):
      page_num = int(self.kwargs['page']) if 'page' in self.kwargs else 1
      page_size = int(self.kwargs["page_size"]) if "page_size" in self.kwargs else settings.DEFAULT_NUMBER_OF_SHOWN_MESSAGES
      # print("page_size=", page_size)
      posts = Post.objects.select_related('first_message').annotate(num_messages=Count("message")) \
                  .all().order_by('-first_message__date')
      ptor = Paginator(posts, page_size, reverse_link='posts:page')
      # if page_num > ptor.num_pages:
      #   return redirect(reverse('posts:page', args=[ptor.num_pages]) + '?' + urlencode({'page_size': page_size}))
      page = ptor.get_page_data(page_num)
      return {"page": page}


class PostDisplayView(LoginRequiredMixin, generic.DetailView):
    model = Post

    def get_context_data(self, **kwargs):
      post_id = self.kwargs['pk']
      object = get_object_or_404(Post, pk=post_id)
      replies = Message.objects.filter(post=post_id, first_of_post=None).all()

    #   for r in replies:
    #     print(r.content)

      return {
         'object': object,
         'replies': replies,
         'nreplies': replies.count(),
         'comment_form': CommentForm(),
         'reply_form': MessageForm(),
      }


class PostCreateView(LoginRequiredMixin, generic.CreateView):
    model = Post

    def get(self, request):
      post_form = PostForm()
      message_form = MessageForm()
      return render(request, "forum/post_form.html", context={'post_form': post_form, 'message_form': message_form})

    def post(self, request):
      post_form = PostForm(request.POST)
      message_form = MessageForm(request.POST)
      post = message = None
      if post_form.is_valid() and message_form.is_valid():
        try:
            author = Member.objects.only('id').get(id=request.user.id)
            message_form.instance.author_id = author.id
            with transaction.atomic():
                message = message_form.save()
                post_form.instance.first_message = message
                post = post_form.save()
                message.post = post
                message.save()
            return redirect("forum:display", post.id)
        except Exception as e:
            if message and message.id:  # message saved, delete it
              message.delete()
            if post and post.id:  # post saved, delete it
              post.delete()
            raise e


class PostEditView(LoginRequiredMixin, generic.UpdateView):
    model = Post
    form_class = PostForm

    def get(self, request, pk):
      instance = get_object_or_404(Post, pk=pk)
      post_form = PostForm(instance=instance)
      message_form = MessageForm(instance=instance.first_message)
      return render(request, "forum/post_form.html",
                    context={'post_form': post_form, 'message_form': message_form, 'post': instance})

    def post(self, request, pk):
      instance = get_object_or_404(Post, pk=pk)
      if instance.first_message.author.id != request.user.id:
        raise PermissionError("Only authors can edit their posts")

      post_form = PostForm(request.POST, instance=instance)
      message_form = MessageForm(request.POST, instance=instance.first_message)
      if post_form.is_valid() and message_form.is_valid():
        message_form.save()
        post = post_form.save()
        return redirect("forum:display", post.id)


@login_required
def delete_post(request, pk):
  post = get_object_or_404(Post, pk=pk)
  post.delete()
  return redirect('forum:list')


@login_required
def add_reply(request, pk):
  reply = MessageForm(request.POST)
  reply.instance.post_id = pk
  reply.instance.author_id = request.user.id
  reply.save()
  return redirect(reverse("forum:display", args=[pk]))


@login_required
def edit_reply(request, reply):
  if is_ajax(request):
    instance = get_object_or_404(Message, pk=reply)
    form = MessageForm(request.POST, instance=instance)
    if form.is_valid():
      replyobj = form.save()
      return JsonResponse({"reply_id": replyobj.id, "reply_str": replyobj.content}, status=200)
    else:
      errors = form.errors.as_json()
      return JsonResponse({"errors": errors}, status=400)
  raise ValidationError("Forbidden non ajax request")


@csrf_exempt
@login_required
def delete_reply(request, reply):
    if is_ajax(request):
        reply = get_object_or_404(Message, pk=reply)
        if (Post.objects.filter(first_message=reply).exists()):
          raise ValidationError(_("Can't delete the first message of a thread!"))
        id = reply.id
        reply.delete()
        return JsonResponse({"reply_id": id}, status=200)
    raise ValidationError("Forbidden non ajax request")


class CommentCreateView(LoginRequiredMixin, generic.CreateView):
    model = Comment
    form_class = CommentForm

    def post(self, request, message_id):
      message = get_object_or_404(Message, pk=message_id)
      form = CommentForm(request.POST)
      if form.is_valid():
        form.instance.author_id = request.user.id
        form.instance.message_id = message_id
        form.save()
        return redirect("forum:display", message.post.id)


class CommentEditView(LoginRequiredMixin, generic.UpdateView):
    model = Comment
    form_class = CommentForm

    def post(self, request, pk):
      if is_ajax(request):
          comment = get_object_or_404(Comment, pk=pk)
          # create a form instance from the request and save it
          form = CommentForm(request.POST, instance=comment)
          if form.is_valid():
            comment = form.save()
            return JsonResponse({"comment_id": comment.id, "comment_str": comment.content}, status=200)
          else:
            errors = form.errors.as_json()
            return JsonResponse({"errors": errors}, status=400)
      raise ValidationError("Forbidden non ajax request")


@csrf_exempt
@login_required
def delete_comment(request, pk):
    if is_ajax(request):
        comment = get_object_or_404(Comment, pk=pk)
        id = comment.id
        comment.delete()
        return JsonResponse({"comment_id": id}, status=200)
    raise ValidationError("Forbidden non ajax request")
