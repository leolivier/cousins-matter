from django.template import Library, Node, Variable, TemplateSyntaxError
from django.template.response import TemplateResponse
from django.conf import settings
from django.urls import reverse, resolve, NoReverseMatch

register = Library()


class ViewNode(Node):
    def __init__(self, url_or_view, args, kwargs):
        self.url_or_view = url_or_view
        self.args = args
        self.kwargs = kwargs

    def render(self, context):
        if 'request' not in context:
            raise TemplateSyntaxError("No request has been made.")

        url_or_view = Variable(self.url_or_view).resolve(context)
        try:
            view, args, kwargs = resolve(reverse(url_or_view))
        except NoReverseMatch:
            view, args, kwargs = resolve(url_or_view)

        try:
            if callable(view):
                self.args += args
                self.kwargs.update(**kwargs)
                return (view(context['request'], *self.args, **self.kwargs)
                        .rendered_content)
            raise "%r is not callable" % view
        except:
            if settings.DEBUG:
                raise
        return None

@register.tag(name='include_view')
def do_view(parser, token):
    args, kwargs, tokens = [], {}, token.split_contents()
    if len(tokens) < 2:
        raise TemplateSyntaxError(
            f"{token.contents.split()[0]} tag requires one or more arguments")

    for t in tokens[2:]:
        kw = t.find("=")
        args.append(t) if kw == -1 else kwargs.update({str(t[:kw]): t[kw+1:]})
    return ViewNode(tokens[1], args, kwargs)