from django.db import transaction
from django.contrib.auth.decorators import login_required
from ..models import Post, Message, Comment
from members.models import Member


@login_required
def test_create_posts(request, num_posts):
  connected_member = Member.objects.get(id=request.user.id)
  for i in range(num_posts):
    with transaction.atomic():
      message = Message(content=f"a test message #{i}", author=connected_member)
      message.save()
      post = Post(title=f"a new post #{i}", first_message=message)
      post.save()
      message.post = post
      message.save()


@login_required
def test_create_replies(request, num_replies):
  connected_member = Member.objects.get(id=request.user.id)
  with transaction.atomic():
    message = Message(content="the first message", author=connected_member)
    message.save()
    post = Post(title="a post for testing a lot of replies", first_message=message)
    post.save()
    message.post = post
    message.save()
  for i in range(num_replies):
    Message(content=f"a test reply #{i}", post=post, author=connected_member).save()


@login_required
def test_create_comments(request, num_comments):
  connected_member = Member.objects.get(id=request.user.id)
  with transaction.atomic():
    message = Message(content="the commented message", author=connected_member)
    message.save()
    post = Post(title="a post for testing a lot of comments", first_message=message)
    post.save()
    message.post = post
    message.save()
  for i in range(num_comments):
    Comment(content=f"a test comment #{i}", author=connected_member, message=message).save()
