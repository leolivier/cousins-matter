from django import forms
from django.utils.translation import gettext as _
from .validators import validate_zipfile_extension
from .models import Photo, Gallery
from cm_main.widgets import RichTextarea


class BulkUploadPhotosForm(forms.Form):
    zipfile = forms.FileField(label=_('Zip file'),
                              help_text=_('The zip file containing the photos to upload. All folders will be created as galleries and photos in these folders added to the galleries. All photos must be in folders.'),  # noqa E501
                              validators=[validate_zipfile_extension],
                              widget=forms.FileInput(attrs={'accept': ".zip"})
                              )


class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ["name", "description", "image", "date", "gallery"]
        widgets = {
            "description": RichTextarea(),
        }


class GalleryForm(forms.ModelForm):
    class Meta:
        model = Gallery
        fields = ["name", "description", "cover", "parent"]
        widgets = {
            "description": RichTextarea(),
        }
