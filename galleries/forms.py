from django import forms
from django.conf import settings
from django.utils.translation import gettext as _
from .validators import validate_zipfile_extension
from .models import Photo, Gallery
from cm_main.widgets import RichTextarea
from cousinsmatter.utils import check_file_size


def check_zip_size(file):
    return check_file_size(file, settings.MAX_GALLERY_BULK_UPLOAD_SIZE)


class BulkUploadPhotosForm(forms.Form):
    zipfile = forms.FileField(label=_('Zip file'),
                              help_text=_('The zip file containing the photos to upload. All folders will be created as galleries and photos in these folders added to the galleries. All photos must be in folders.'),  # noqa E501
                              validators=[validate_zipfile_extension, check_zip_size],
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
