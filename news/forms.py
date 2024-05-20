from django.forms import ModelForm
from cm_main.widgets import RichTextarea
from .models import NewsContent, News, Comment


class NewsContentForm(ModelForm):
  class Meta:
    model = NewsContent
    fields = ['content']
    widgets = {
        'content': RichTextarea(),
    }


class NewsForm(ModelForm):
  class Meta:
    model = News
    fields = ['title']


class CommentForm(ModelForm):
  class Meta:
    model = Comment
    fields = ['content']
