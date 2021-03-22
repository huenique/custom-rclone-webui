from django import forms

RCLONE_STORAGE_TYPES = [('drive', 'Google Drive')]


class UploadForm(forms.Form):
    upload = forms.FileField(widget=forms.ClearableFileInput(
        attrs={'multiple': True}))


class NewRemoteForm(forms.Form):
    storage_name = forms.CharField(label='Name of the Storage', required=True)
    storage_type = forms.ChoiceField(label='Storage Type',
                                     required=True,
                                     widget=forms.RadioSelect(),
                                     choices=RCLONE_STORAGE_TYPES)


class RemoteDriveOptions(forms.Form):
    client_id = forms.CharField(label='Enter Client ID', required=True)
    client_secret = forms.CharField(label='Enter Client Secret', required=True)

    def clean(self):
        cleaned_data = super(RemoteDriveOptions, self).clean()
        client_id = cleaned_data.get('client_id')
        client_secret = cleaned_data.get('client_secret')

        if not client_id and not client_secret:
            raise forms.ValidationError(
                'Form validation failed! Important fields were missing or incorrect.'
            )
