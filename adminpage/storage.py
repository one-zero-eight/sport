from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


class CustomManifestStaticFilesStorage(ManifestStaticFilesStorage):
    def url(self, name, force=False):
        if name == "plupload":
            return None  # Fix error with smartfields
        return super().url(name, force)
