import os
from django import forms
from django.forms import ModelForm, Form
from django.forms import ValidationError
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _, get_language

from captcha.fields import CaptchaField

from cm_main.widgets import RichTextarea
from .models import Member, Address, Family
from .widgets import FieldLinkWrapper
from cm_main.utils import check_file_size


class MemberFormMixin:
  def initialize_fields(self, *args, **kwargs):
    can_change_family = self.instance and self.instance.family
    self.fields["family"].widget = FieldLinkWrapper(
      self.fields["family"].widget,
      can_add_related=True,
      can_change_related=can_change_family,
    )
    can_change_address = self.instance and self.instance.address
    self.fields["address"].widget = FieldLinkWrapper(
      self.fields["address"].widget,
      can_add_related=True,
      can_change_related=can_change_address,
    )
    # force first and last name to be required  # TODO: is this useful?
    self.fields["first_name"].required = True
    self.fields["last_name"].required = True
    # we don't need the password field, it's useless and harmful
    # the generated code is wrong (it creates a link to f"../../{self.instance.pk}/password/")
    # which is not what we want, and furthermore we have a link to change password in the template
    # so we remove the password field
    if "password" in self.fields:
      del self.fields["password"]
    # description is a rich text field
    if "description" in self.fields:
      self.fields["description"].widget = RichTextarea()
    # remove death date field from profile page
    if isinstance(self, MemberUpdateForm) and self.is_profile_form:
      del self.fields["deathdate"]

    if "birthdate" in self.fields:
      self.fields["birthdate"].widget = forms.DateInput(attrs={'type': 'date'})
    if "deathdate" in self.fields:
      self.fields["deathdate"].widget = forms.DateInput(attrs={'type': 'date'})

  def clean_avatar(self):
    avatar = self.cleaned_data["avatar"]
    # print(f"Validating avatar for {self.instance.full_name} in {avatar}")
    if "avatar" not in self.changed_data:
      # print("No change in avatar, skipping validation")
      return avatar
    try:
      # issue #150: avatar can be a boolean when trying to delete it
      if type(avatar) is bool and not avatar:
        self.instance.delete_avatar()  # this will delete the avatar and the minified avatar:
        return None
      # validate file size
      if len(avatar) > settings.AVATAR_MAX_SIZE:
        nMB = settings.AVATAR_MAX_SIZE / 1024 / 1024
        raise ValidationError(f"Avatar file size may not exceed {nMB} bytes.")

    except AttributeError:
      """
        Handles case when we are updating the member
        and do not supply a new avatar
        """
      pass

    return avatar

  def init_privacy_field(self):
    "Initialize the privacy consent field with a link to the privacy policy and force it to be required"
    privacy_url = "/" + get_language() + settings.PRIVACY_URL
    self.fields["privacy_consent"].label = mark_safe(
      _("By checking this box, you agree to this site's <a target='blank' href='%(privacy_url)s'>privacy policy</a>")
      % {"privacy_url": privacy_url}
    )
    self.fields["privacy_consent"].required = True


class MemberRegistrationForm(MemberFormMixin, UserCreationForm):
  class Meta:
    model = Member
    localized_fields = "__all__"
    fields = [
      "username",
      "email",
      "password1",
      "password2",
      "first_name",
      "last_name",
      "avatar",
      "birthdate",
      "address",
      "phone",
      "description",
      "hobbies",
      "website",
      "family",
      "privacy_consent",
    ]

  def __init__(self, *args, **kwargs):
    super(UserCreationForm, self).__init__(*args, **kwargs)
    self.initialize_fields(*args, **kwargs)
    # force email to be required  # TODO: is this useful?
    self.fields["email"].required = True
    self.init_privacy_field()


class MemberUpdateForm(MemberFormMixin, UserChangeForm):
  class Meta:
    model = Member
    localized_fields = "__all__"
    fields = [
      "username",
      "email",
      "first_name",
      "last_name",
      "avatar",
      "birthdate",
      "address",
      "phone",
      "description",
      "hobbies",
      "website",
      "family",
      "deathdate",
      "privacy_consent",
    ]
    exclude = ["password"]

  def __init__(self, *args, **kwargs):
    self.user = kwargs.pop("user", None)
    self.is_profile_form = kwargs.pop("is_profile", False)
    super().__init__(*args, **kwargs)
    self.initialize_fields(*args, **kwargs)
    self.init_privacy_field()
    # restrict deathdate to superusers or managed members
    if self.user and self.instance.is_active and not self.user.is_superuser:
      if "deathdate" in self.fields:
        del self.fields["deathdate"]
      if "is_dead" in self.fields:
        del self.fields["is_dead"]


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
    self.fields["parent"].widget = FieldLinkWrapper(
      self.fields["parent"].widget,
      can_add_related=True,
      can_change_related=can_change_parent,
      name="parent-family",
    )

  def clean_name(self):
    name = self.cleaned_data["name"].strip()
    if not name:
      raise ValidationError(_("Family name cannot be empty"), code="empty")
    return name


class MemberInvitationForm(Form):
  invited = forms.CharField(
    label=_("Name of the invited person (will appear in the received email)"),
    max_length=75,
  )
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
    raise ValidationError("File must be a csv file")


def check_csv_file_size(file):
  return check_file_size(file, settings.MAX_CSV_FILE_SIZE)


class CSVImportMembersForm(forms.Form):
  csv_file = forms.FileField(
    label=_("CSV file"),
    help_text=_("The CSV file containing the members to import."),
    validators=[validate_csv_extension, check_csv_file_size],
    widget=forms.FileInput(attrs={"accept": ".csv"}),
  )
  activate_users = forms.BooleanField(label=_("Automatically activate imported users"), required=False)

class NotifyDeathForm(forms.Form):
  deathdate = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}),
                              label=_("Date of Death"),
                              required=True)
  message = forms.CharField(widget=forms.Textarea(attrs={"rows": 4, "cols": 50, "placeholder": _("Any additional information...")}),
                            label=_("Message (Optional)"),
                            required=False)