import os

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.db import models


def user_directory_path(instance, filename):
    """
    Creates a new directory for chosen files.
    """
    # TODO: Obtain an upload path assigned to the user.
    # Upload file to MEDIA_ROOT/user_<id>/<filename>
    # return "Users/user_{0}/{1}".format(instance.owner.id, filename)
    return f'{filename}'


class OverwriteStorage(FileSystemStorage):
    """
    Let the Django FileField overwrite files with the same name.
    """
    def get_available_name(self, name, max_length=None):
        try:
            self.delete(name)
            Upload.objects.get(file=name).delete()
        except ObjectDoesNotExist:
            pass
        return super(OverwriteStorage,
                     self).get_available_name(name, max_length)


class Upload(models.Model):
    """
    Model for any and all file uploads.
    """
    file = models.FileField(upload_to=user_directory_path,
                            storage=OverwriteStorage())
    last_modified = models.DateTimeField(auto_now=True, null=True)
    deletion = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    @property
    def file_name(self):
        return os.path.basename(self.file.name)
