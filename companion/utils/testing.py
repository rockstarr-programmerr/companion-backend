import shutil

from django.conf import settings
from rest_framework.test import APITestCase


class MediaTestCase(APITestCase):
    """
    Class for testcases that create media like user avatar, event QR code, .etc
    It will create temporary directory for these media, and delete it after testing complete
    so that media created by tests will not persist.
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._media_root = settings.MEDIA_ROOT
        cls._temp_media_root = settings.MEDIA_ROOT / 'test_media_feel_free_to_delete'
        settings.MEDIA_ROOT = cls._temp_media_root

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        settings.MEDIA_ROOT = cls._media_root
        shutil.rmtree(cls._temp_media_root, ignore_errors=True)
