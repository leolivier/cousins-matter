from pprint import pprint
from django.forms import ModelForm
from django.forms import ValidationError
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import Member, Address, Family
from .widgets import FieldLinkWrapper
from cousinsmatter import settings

class MemberUpdateForm(ModelForm):
  class Meta:
    model = Member
    localized_fields = "__all__"
    exclude=["managing_account", "account"]

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    can_change_family = self.instance and self.instance.family
    self.fields['family'].widget = FieldLinkWrapper(self.fields['family'].widget, can_add_related=True, can_change_related=can_change_family)
    can_change_address = self.instance and self.instance.address
    self.fields['address'].widget = FieldLinkWrapper(self.fields['address'].widget, can_add_related=True, can_change_related=can_change_address)

  def clean_avatar(self):
    avatar = self.cleaned_data['avatar']
    # print(f"Validating avatar for {self.instance.get_full_name()} in {avatar}")
    if 'avatar' not in self.changed_data:
      print("No change in avatar, skipping validation")
      return avatar
    try:
      #validate file size
      if len(avatar) > settings.AVATAR_MAX_SIZE:
          nMB = settings.AVATAR_MAX_SIZE / 1024 / 1024
          raise ValidationError(
              f'Avatar file size may not exceed {nMB} bytes.')

    except AttributeError:
        """
        Handles case when we are updating the member
        and do not supply a new avatar
        """
        pass

    return avatar

  def clean_managing_account(self):  # managing_account is excluded from this form, so this useless!
    account = self.cleaned_data.get("account")
    raise ValidationError("We should never go there!!!")
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

    
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    can_change_parent = self.instance and self.instance.parent
    self.fields['parent'].widget = FieldLinkWrapper(self.fields['parent'].widget, True, can_change_parent, 
                                                    name="parent-family")
