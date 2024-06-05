# based on https://stackoverflow.com/questions/17178525/django-how-to-include-a-view-from-within-a-template#56476932
# this view and tag allows including a view into another view. see template/cm_main/base.html as an example
# TODO: deliver this as a reusable piece of code
from django.template import Library, Node, Variable, TemplateSyntaxError
from django.conf import settings
from django.urls import reverse, resolve, NoReverseMatch
from django.utils.translation import gettext_lazy as _

register = Library()

default_site_copyright = _('Copyright © 2024 Cousins Matter. All rights reserved.')


class ViewNode(Node):
    def __init__(self, url_or_view, args, kwargs):
        self.url_or_view = url_or_view
        self.args = args
        self.kwargs = kwargs
        self.init = False

    def _resolve_args(self, context):
        # for an unknown reason, the first time, the args are not resolved
        if self.init:
            resolved_args = self.args
            resolved_kwargs = self.kwargs
        else:
            resolved_args = [] if self.args else None
            for arg in self.args:
                resolved_args.append(Variable(arg).resolve(context))
            resolved_kwargs = {} if self.kwargs else None

            for k, v in self.kwargs.items():
                resolved_kwargs[k] = Variable(v).resolve(context)
            self.init = True
        return resolved_args, resolved_kwargs

    def render(self, context):
        if 'request' not in context:
            raise TemplateSyntaxError("No request has been made.")

        url_or_view = Variable(self.url_or_view).resolve(context)
        resolved_args, resolved_kwargs = self._resolve_args(context)
        try:
            view, args, kwargs = resolve(reverse(url_or_view, args=resolved_args, kwargs=resolved_kwargs))
        except NoReverseMatch:
            view, args, kwargs = resolve(url_or_view)

        try:
            if callable(view):
                self.args += args
                self.kwargs.update(**kwargs)
                return (view(context['request'], *self.args, **self.kwargs)
                        .rendered_content)
            raise "%r is not callable" % view
        except Exception:
            if settings.DEBUG:
                raise
        return None


@register.tag(name='cm_tags')
def do_view(parser, token):
    args, kwargs, tokens = [], {}, token.split_contents()
    if len(tokens) < 2:
        raise TemplateSyntaxError(
            f"{token.contents.split()[0]} tag requires one or more arguments")

    for t in tokens[2:]:
        kw = t.find("=")
        args.append(t) if kw == -1 else kwargs.update({str(t[:kw]): t[kw+1:]})
    # print(kwargs)

    return ViewNode(tokens[1], args, kwargs)


@register.simple_tag
def title(title_s):
    return f"{settings.SITE_NAME} - {title_s}"


@register.simple_tag
def site_copyright():
    return settings.SITE_COPYRIGHT if settings.SITE_COPYRIGHT is not None else default_site_copyright


# TODO: test pagination with big lists of objects
@register.inclusion_tag("cm_main/paginate_template.html")
def paginate(page):
    return {
        "page_urls": page.page_links,
        "page_range": page.page_range,
        "first_page_url": page.first_page_link,
        "last_page_url": page.last_page_link,
        "prev_page_url": page.page_links[page.number-page.first-2] if page.has_previous() else None,
        "next_page_url": page.page_links[page.number-page.first] if page.has_next() else None,
        "current_page": page.number,
        "possible_per_pages": page.possible_per_pages,
        "page_size": page.paginator.per_page,
        "num_pages": page.num_pages,
    }
