"""Custom Cloudinary storage selecting resource_type from file extension."""
import os
import cloudinary
import cloudinary.uploader
from cloudinary_storage.storage import MediaCloudinaryStorage, RESOURCE_TYPES


class CustomMediaCloudinaryStorage(MediaCloudinaryStorage):
    """Determine Cloudinary resource_type based on file extension.

    - images -> resource_type='image'
    - videos  -> resource_type='video'
    - others  -> resource_type='raw'
    """

    IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'tiff', 'svg'}
    VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}

    def _get_extension(self, name):
        if not name or '.' not in name:
            return None
        return name.rsplit('.', 1)[-1].lower()

    def _get_resource_type(self, name):
        ext = self._get_extension(name)
        if ext in self.IMAGE_EXTENSIONS:
            return RESOURCE_TYPES['IMAGE']
        if ext in self.VIDEO_EXTENSIONS:
            return RESOURCE_TYPES['VIDEO']
        return RESOURCE_TYPES['RAW']

    def _upload(self, name, content):
        """Upload using the inferred resource_type so Cloudinary doesn't try to validate
        non-image files as images (which caused "Invalid image file")."""
        options = {
            'use_filename': True,
            'resource_type': self._get_resource_type(name),
            'tags': self.TAG,
        }
        folder = os.path.dirname(name)
        if folder:
            options['folder'] = folder

        # For larger video uploads Cloudinary supports chunked upload; the default
        # uploader.upload can handle videos when resource_type='video'.
        return cloudinary.uploader.upload(content, **options)
