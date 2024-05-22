from django.forms import ModelForm
from cm_main.widgets import RichTextarea
from .models import Message, Post, Comment


class MessageForm(ModelForm):
  class Meta:
    model = Message
    fields = ['content']
    widgets = {
        'content': RichTextarea(),
    }


class PostForm(ModelForm):
  class Meta:
    model = Post
    fields = ['title']


class CommentForm(ModelForm):
  class Meta:
    model = Comment
    fields = ['content']
