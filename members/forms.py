from django.forms import ModelForm
from django.contrib.auth.models import User
#from django.utils.translation import gettext as _
from .models import Member, Address, Family

class MemberUpdateForm(ModelForm):
  class Meta:
    model = Member
    localized_fields = "__all__"
    exclude=["managing_account", "account"]

  def clean(self):
    account = self.cleaned_data.get("account")
    if account:  # if we have an account in form, we need to set the managing_account to the same account
      self.cleaned_data['managing_account'] = User.objects.get(id=account.id)
    return super().clean()

class AddressUpdateForm(ModelForm):
  class Meta:
    model = Address
    fields = "__all__"
    localized_fields = "__all__"
    exclude=[]

class FamilyUpdateForm(ModelForm):
  class Meta:
    model = Family
    fields = "__all__"
    localized_fields = "__all__"
    exclude=[]