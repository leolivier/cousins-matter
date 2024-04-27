# based on https://stackoverflow.com/questions/17178525/django-how-to-include-a-view-from-within-a-template#56476932
# this view and tag allows including a view into another view. see template/cm_main/base.html as an example
# TODO: deliver this as a reusable piece of code
from django.template import Library, Node, Variable, TemplateSyntaxError
from django.conf import settings
from django.urls import reverse, resolve, NoReverseMatch

register = Library()


class ViewNode(Node):
    def __init__(self, url_or_view, args, kwargs):
        self.url_or_view = url_or_view
        self.args = args
        self.kwargs = kwargs
        self.init = False

    def render(self, context):
        if 'request' not in context:
            raise TemplateSyntaxError("No request has been made.")

        url_or_view = Variable(self.url_or_view).resolve(context)
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
    # print(kwargs)

    return ViewNode(tokens[1], args, kwargs)