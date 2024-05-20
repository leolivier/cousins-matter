from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from cousinsmatter.utils import is_ajax
from .models import News, NewsContent, Comment
from .forms import NewsContentForm, NewsForm, CommentForm
from members.models import Member


class NewsListView(generic.ListView):
    model = News

    def get_context_data(self, **kwargs):
      page_num = int(self.kwargs['page']) if 'page' in self.kwargs else 1
      ptor = Paginator(News.objects.select_related('first_content').all().order_by('-first_content__date'), 2)
      page = ptor.page(page_num)
      max_pages = 5
      # compute a page range from the initial range + or -max-pages
      page_range = ptor.page_range[max(0, page_num-max_pages-1):min(ptor.num_pages+1, page_num+max_pages)]
      return {
        "object_list": page.object_list,
        "page_range": page_range,
        "current_page": page_num,
        "num_pages": ptor.num_pages,
      }


class NewsDisplayView(generic.DetailView):
    model = News

    def get_context_data(self, **kwargs):
      news_id = self.kwargs['pk']
      object = get_object_or_404(News, pk=news_id)
      replies = NewsContent.objects.filter(news=news_id, news_first=None).all()

      for r in replies:
        print(r.content)

      return {
         'object': object,
         'replies': replies,
         'nreplies': replies.count(),
         'comment_form': CommentForm(),
         'reply_form': NewsContentForm(),
      }


class NewsCreateView(generic.CreateView):
    model = News

    def get(self, request):
      newsform = NewsForm()
      contentform = NewsContentForm()
      return render(request, "news/news_form.html", context={'newsform': newsform, 'contentform': contentform})

    def post(self, request):
      newsform = NewsForm(request.POST)
      contentform = NewsContentForm(request.POST)
      news = content = None
      if newsform.is_valid() and contentform.is_valid():
        try:
            author = Member.objects.only('id').get(account__id=request.user.id)
            contentform.instance.author_id = author.id
            with transaction.atomic():
                content = contentform.save()
                newsform.instance.first_content = content
                news = newsform.save()
                content.news = news
                content.save()
            return redirect("news:display", news.id)
        except Exception as e:
            if content and content.id:  # content saved, delete it
              content.delete()
            if news and news.id:  # news saved, delete it
              news.delete()
            raise e


class NewsEditView(generic.UpdateView):
    model = News
    form_class = NewsForm

    def get(self, request, pk):
      instance = get_object_or_404(News, pk=pk)
      newsform = NewsForm(instance=instance)
      contentform = NewsContentForm(instance=instance.first_content)
      return render(request, "news/news_form.html", context={'newsform': newsform, 'contentform': contentform})

    def post(self, request, pk):
      instance = get_object_or_404(News, pk=pk)
      if instance.first_content.author.account.id != request.user.id:
        raise PermissionError("Only authors can edit their news")

      newsform = NewsForm(request.POST, instance=instance)
      contentform = NewsContentForm(request.POST, instance=instance.first_content)
      if newsform.is_valid() and contentform.is_valid():
        contentform.save()
        news = newsform.save()
        return redirect("news:display", news.id)


def add_reply(request, pk):
  reply = NewsContentForm(request.POST)
  reply.instance.news_id = pk
  author = Member.objects.only('id').get(account__id=request.user.id)
  reply.instance.author_id = author.id
  reply.save()
  return redirect(reverse("news:display", args=[pk]))


def edit_reply(request, reply):
  instance = get_object_or_404(NewsContent, pk=reply)
  form = NewsContentForm(request.POST, instance=instance)
  form.save()
  return redirect(reverse("news:display", instance.news.id))


class NewsDeleteView(generic.DeleteView):
    model = News


class CommentCreateView(generic.CreateView):
    model = Comment
    form_class = CommentForm

    def post(self, request, content_id):
      form = CommentForm(request.POST)
      if form.is_valid():
        author = Member.objects.get(account__id=request.user.id)
        form.instance.author_id = author.id
        form.instance.news_content_id = content_id
        form.save()
        news = News.objects.only('id').get(first_content__id=content_id)
        return redirect("news:display", news.id)


class CommentEditView(generic.UpdateView):
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
      raise ValueError("Forbidden non ajax request")


@csrf_exempt
def delete_comment(request, pk):
    if is_ajax(request):
        comment = get_object_or_404(Comment, pk=pk)
        comment.delete()
        return JsonResponse({"comment_id": comment.id}, status=200)
    raise ValueError("Forbidden non ajax request")
