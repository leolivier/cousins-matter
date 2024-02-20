from django.forms import ModelForm
from django.utils.translation import gettext as _
from .models import Member

class MemberForm(ModelForm):
  class Meta:
    model = Member
    fields = "__all__"
    localized_fields = "__all__"
    #exclude=[]
