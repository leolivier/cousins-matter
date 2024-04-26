from django import forms
from django.utils.translation import gettext as _
from .validators import validate_zipfile_extension

class BulkUploadPhotosForm(forms.Form):
    zipfile = forms.FileField(label=_('Zip file'), 
                              help_text=_('The zip file containing the photos to upload. All folders will be created as galleries and photos in these folders added to the galleries. All photos must be in folders.'),
                              validators=[validate_zipfile_extension],
                              widget=forms.FileInput(attrs={ 'accept': ".zip"})
                            )
    