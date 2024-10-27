import os
from django import forms
from django.forms import ModelForm, Form
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from captcha.fields import CaptchaField

from cm_main.widgets import RichTextarea
from .models import Member, Address, Family
from .widgets import FieldLinkWrapper
from cousinsmatter.utils import check_file_size


class MemberFormMixin():
  def initialize_fields(self, *args, **kwargs):
    can_change_family = self.instance and self.instance.family
    self.fields['family'].widget = FieldLinkWrapper(self.fields['family'].widget, can_add_related=True,
                                                    can_change_related=can_change_family)
    can_change_address = self.instance and self.instance.address
    self.fields['address'].widget = FieldLinkWrapper(self.fields['address'].widget, can_add_related=True,
                                                     can_change_related=can_change_address)
    # force first and last name to be required  # TODO: is this useful?
    self.fields['first_name'].required = True
    self.fields['last_name'].required = True
    # we don't need the password field, it's useless and harmful
    # the generated code is wrong (it creates a link to f"../../{self.instance.pk}/password/")
    # which is not what we want, and furthermore we have a link to change password in the template
    # so we remove the password field
    if 'password' in self.fields:
      del self.fields['password']
    # description is a rich text field
    if 'description' in self.fields:
      self.fields['description'].widget = RichTextarea()

  def clean_avatar(self):
    avatar = self.cleaned_data['avatar']
    # print(f"Validating avatar for {self.instance.full_name} in {avatar}")
    if 'avatar' not in self.changed_data:
      # print("No change in avatar, skipping validation")
      return avatar
    try:
      # validate file size
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


class MemberRegistrationForm(MemberFormMixin, UserCreationForm):
  class Meta:
    model = Member
    localized_fields = "__all__"
    fields = ['username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'avatar',
              'birthdate', 'address', 'phone', 'description', 'hobbies', 'website', 'family', 'privacy_consent']

  def __init__(self, *args, **kwargs):
    super(UserCreationForm, self).__init__(*args, **kwargs)
    self.initialize_fields(*args, **kwargs)
    # force email to be required  # TODO: is this useful?
    self.fields['email'].required = True
    privacy_url = settings.PRIVACY_URL
    self.fields['privacy_consent'].help_text = \
      _(f"By checking this box, you consent to the <a target='blank' href='{privacy_url}'>privacy policy</a> of this site")
    self.fields['privacy_consent'].required = True


class MemberUpdateForm(MemberFormMixin, UserChangeForm):
  class Meta:
    model = Member
    localized_fields = "__all__"
    fields = ['username', 'email', 'first_name', 'last_name', 'avatar',
              'birthdate', 'address', 'phone', 'description', 'hobbies', 'website', 'family']
    exclude = ['password']

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.initialize_fields(*args, **kwargs)


class AddressUpdateForm(ModelForm):
  class Meta:
    model = Address
    fields = "__all__"
    localized_fields = "__all__"
    exclude = []


class FamilyUpdateForm(ModelForm):
  class Meta:
    model = Family
    fields = "__all__"
    localized_fields = "__all__"
    exclude = []

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    can_change_parent = self.instance and self.instance.parent
    self.fields['parent'].widget = FieldLinkWrapper(self.fields['parent'].widget, True, can_change_parent,
                                                    name="parent-family")


class MemberInvitationForm(Form):
  invited = forms.CharField(label=_("Name of the invited person (will appear in the received email)"), max_length=75)
  email = forms.EmailField(label=_("Email to send invitation"), max_length=254)


class RegistrationRequestForm(Form):
  name = forms.CharField(label=_("Your name"), max_length=254)
  email = forms.EmailField(label=_("Email where you will receive the link"), max_length=254)
  message = forms.CharField(label=_("Message to the administrator"), widget=forms.Textarea, max_length=2000)
  captcha = CaptchaField(label=_("Captcha (click on the image to refresh if you can't read it)"))


def validate_csv_extension(value):
    from django.core.exceptions import ValidationError
    ext = os.path.splitext(value.name)[1]
    if ext.lower() != ".csv":
        raise ValidationError('File must be a csv file')


def check_csv_file_size(file):
  return check_file_size(file, settings.MAX_CSV_FILE_SIZE)


class CSVImportMembersForm(forms.Form):
    csv_file = forms.FileField(label=_('CSV file'),
                               help_text=_("The CSV file containing the members to import."),
                               validators=[validate_csv_extension, check_csv_file_size],
                               widget=forms.FileInput(attrs={'accept': ".csv"})
                               )
    activate_users = forms.BooleanField(label=_('Automatically activate imported users'), required=False)
