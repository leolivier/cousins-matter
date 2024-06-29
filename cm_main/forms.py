from django import forms
from django.utils.translation import gettext_lazy as _

from cm_main.widgets import RichTextarea


class ContactForm(forms.Form):
    message = forms.CharField(label=_("Your message"), widget=RichTextarea, max_length=20000,
                              help_text=_("Please keep it short and avoid images."))
    attachment = forms.FileField(label=_('Attach file'), required=False,
                                 help_text=_("You can attach a file here if needed"),
                                 )
