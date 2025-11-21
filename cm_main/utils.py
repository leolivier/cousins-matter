# util functions for cousinsmatter app
import logging
import math
import os
import shutil
from contextlib import contextmanager
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageOps, ImageFile
from pathlib import PosixPath

# import pprint
import sys
import unicodedata
from urllib.parse import urlencode, quote

from django.conf import settings
from django.core import paginator
from django.core.exceptions import PermissionDenied
from django.core.files.storage import FileSystemStorage, default_storage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import connections, models
from django.forms import ValidationError
from django.urls import reverse
from django.utils import formats
from django.utils.translation import gettext as _, get_language, gettext_lazy

from cousinsmatter.context_processors import override_settings


# issue #120 try to avoid error about truncated images when creating thumbnails
ImageFile.LOAD_TRUNCATED_IMAGES = True

logger = logging.getLogger(__name__)

# terrible hack to check if we are in testing mode!!!
IS_TESTING = None


def is_testing():
    global IS_TESTING
    if IS_TESTING is not None:
        return IS_TESTING
    IS_TESTING = False
    for connection in connections.all():
        # print(f"searching test in {connection.settings_dict['NAME']}...")
        if not isinstance(connection.settings_dict["NAME"], PosixPath):
            # print("found")
            IS_TESTING = True
            break
    # print("no test connection found")
    return IS_TESTING


def get_test_absolute_url(url):
    return "http://testserver%s" % (url)


def is_ajax(request):
    return request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"


def assert_request_is_ajax(request):
    if not is_ajax(request):
        raise ValidationError("Forbidden non ajax request")


def check_file_size(file, limit):
    if file.size > limit:
        limitmb = math.floor(limit * 100 / (1024 * 1024)) / 100
        sizemb = math.floor(file.size * 100 / (1024 * 1024)) / 100
        filename = file.name
        raise ValidationError(
            _(
                "Uploaded file %(filename)s is too big (%(sizemb)sMB), maximum is %(limitmb)sMB."
            )
            % {"filename": filename, "sizemb": sizemb, "limitmb": limitmb}
        )


class PageOutOfBounds(ValueError):
    def __init__(self, redirect_to):
        self.redirect_to = redirect_to


class Paginator(paginator.Paginator):
    possible_per_pages = [10, 25, 50, 100]
    max_pages = 2  # on both sides of the current page link

    def __init__(self, query_set, per_page, reverse_link=None, compute_link=None):
        # example of compute_link=lambda page: reverse('members:members_page', args=[gallery_id, page]))
        if not reverse_link and not callable(compute_link):
            raise TypeError(
                "reverse_link not provided and compute_link is not callable"
            )
        # if reverse_link and callable(compute_link):  # see _get_link, choice is compute_link first
        #     raise TypeError("reverse_link provided and compute_link is callable: which one to choose?")
        super().__init__(query_set, per_page)
        self.reverse_link = reverse_link
        self.compute_link = compute_link

    def _get_link(self, idx):
        return (
            self.compute_link(idx)
            if self.compute_link
            else reverse(self.reverse_link, args=[idx])
        )

    def get_page_data(self, page_num, group_by=None):
        page_num = min(page_num, self.num_pages)
        page = self.page(page_num)
        # compute a page range from the initial range + or -max-pages
        page.first = max(0, page_num - self.max_pages - 1)
        page.last = min(self.num_pages + 1, page_num + self.max_pages)
        if page.first == 0:
            page.last = min(self.num_pages, 2 * self.max_pages) + 1
        elif page.last == self.num_pages + 1:
            page.first = max(0, page.last - 2 * self.max_pages - 1)
        page.page_range = self.page_range[page.first : page.last]
        page.num_pages = self.num_pages
        # compute page links
        page.page_links = [self._get_link(i) for i in page.page_range]
        page.first_page_link = self._get_link(1)
        page.last_page_link = self._get_link(self.num_pages)
        page.possible_per_pages = self.possible_per_pages
        if group_by:
            grouped_object_list = {}
            for obj in page.object_list:
                if group_by not in obj.__dict__:
                    raise ValueError(f"Object {obj} has no attribute {group_by}")
                group = getattr(obj, group_by)
                if group not in grouped_object_list:
                    grouped_object_list[group] = []
                grouped_object_list[group].append(obj)
            page.object_list = grouped_object_list

        # pprint.pprint(vars(page))
        return page

    @staticmethod
    def get_page(
        request,
        object_list,
        page_num,
        reverse_link=None,
        compute_link=None,
        default_page_size=100,
        group_by=None,
    ):
        page_size = (
            int(request.GET["page_size"])
            if "page_size" in request.GET
            else default_page_size
        )

        ptor = Paginator(
            object_list, page_size, reverse_link=reverse_link, compute_link=compute_link
        )
        page_num = page_num or ptor.num_pages
        if page_num > ptor.num_pages:
            url = ptor._get_link(ptor.num_pages)
            url += ("&" if "?" in url else "?") + urlencode({"page_size": page_size})
            raise PageOutOfBounds(url)
        return ptor.get_page_data(page_num, group_by=group_by)


@contextmanager
def temporary_log_level(logger, level):
    original_level = logger.level
    logger.setLevel(level)
    try:
        yield
    finally:
        logger.setLevel(original_level)


def remove_accents(input_str):
    """remove accents from a string, including diacritical marks"""
    nfkd_form = unicodedata.normalize("NFKD", input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])


def create_image(image_file, content_type="image/jpeg"):
    """
    Create a Django InMemoryUploadedFile object from a local image file.

    Args:
        image_file: local image file
        content_type: MIME type of the image file (default: 'image/jpeg')

    Returns:
        InMemoryUploadedFile ready to be processed by Django
    """
    membuf = BytesIO()
    with Image.open(image_file) as img:
        img.save(membuf, format="JPEG", quality=90)
        membuf.seek(0)
        size = sys.getsizeof(membuf)
        return InMemoryUploadedFile(
            membuf, "ImageField", os.path.basename(image_file), content_type, size, None
        )


def test_resource_full_path(image_file_basename, file__):
    return os.path.join(os.path.dirname(file__), "resources", image_file_basename)


def create_test_image(file__, image_file_basename, content_type="image/jpeg"):
    image_file = test_resource_full_path(image_file_basename, file__)
    return create_image(image_file, content_type)


@contextmanager
def set_test_media_root(test_file):
    """
    Context manager to set the MEDIA_ROOT to a temporary directory
    within the test file's directory. This is useful for tests that
    need to write files to the media directory. The temporary
    directory is automatically deleted after the test is complete.

    Args:
        test_file: The current test file.

    Yields:
        None
    """
    test_file = os.path.relpath(test_file, settings.BASE_DIR)
    # test_media_root = os.path.join(os.path.dirname(test_file), "media")
    # os.makedirs(test_media_root, exist_ok=True)
    submedia_reltestdir = "test_cfyguihjknmlnjbhg"
    test_media_root = os.path.join(settings.MEDIA_REL, submedia_reltestdir)
    dst = default_storage
    if "location" in dst.__dict__:
        old_storage_location = dst.location
    try:
        with override_settings(MEDIA_ROOT=test_media_root):
            if "location" in dst.__dict__:
                dst.location = test_media_root
            yield
    finally:
        # storage_rmtree(dst, submedia_reltestdir)
        if "location" in dst.__dict__:
            dst.location = old_storage_location
        if os.path.isdir(test_media_root):
            shutil.rmtree(test_media_root)


def test_media_root_decorator(test_file):
    """
    Decorator that sets the MEDIA_ROOT to a temporary directory
    within the test file's directory during the test. This is useful
    for tests that need to write files to the media directory. The
    temporary directory is automatically deleted after the test is
    complete.
    """

    def decorator(cls):
        orig_setUp = cls.setUp
        orig_tearDown = cls.tearDown

        def setUp(self, *args, **kwargs):
            self.test_media_root_context = set_test_media_root(test_file)
            self.test_media_root_context.__enter__()
            orig_setUp(self, *args, **kwargs)

        def tearDown(self, *args, **kwargs):
            orig_tearDown(self, *args, **kwargs)
            self.test_media_root_context.__exit__(None, None, None)

        cls.setUp = setUp
        cls.tearDown = tearDown
        return cls

    return decorator


def allowed_date_formats():
    """
    Returns a list of date formats that are expected to be valid for the current language.
    The formats are those that are expected for DATETIME_INPUT_FORMATS in the current locale.
    Formats that include seconds or microseconds are removed from the list.
    """
    current_language = get_language()  # Retrieves the active locale, e.g. 'fr'.
    # Retrieves the list of expected date formats for the current locale
    # Ex for 'fr': ['%d/%m/%Y', '%d.%m.%Y', '%d-%m-%Y', ...]
    date_formats = formats.get_format("DATETIME_INPUT_FORMATS", lang=current_language)
    # remove formats with seconds and microseconds
    date_formats = [
        date_format
        for date_format in date_formats
        if not date_format.endswith("%f") and not date_format.endswith("%S")
    ]

    return date_formats


def parse_locale_date(date_string_to_parse):
    parsed_datetime = None
    date_formats = allowed_date_formats()

    for date_format in date_formats:
        try:
            # Try parsing the string with the current format
            parsed_datetime = datetime.strptime(date_string_to_parse, date_format)
            # If we succeed, we have our date and stop the loop.
            break
        except (ValueError, TypeError):
            # If the format doesn't match, continue with the next one
            continue

    if parsed_datetime:
        return parsed_datetime
    else:
        translated_date_formats = [
            translate_date_format(date_format) for date_format in date_formats
        ]
        raise ValidationError(
            _(
                "Date '%(date_string_to_parse)s' does not match any expected format: %(translated_date_formats)s."
            )
            % {
                "date_string_to_parse": date_string_to_parse,
                "translated_date_formats": translated_date_formats,
            }
        )


# Listing strftime format codes for makemessages
FORMAT_CODE_DESCRIPTIONS = {
    "%d": gettext_lazy("%%d"),
    "%m": gettext_lazy("%m"),
    "%Y": gettext_lazy("%Y"),
    "%y": gettext_lazy("%y"),
    "%H": gettext_lazy("%H"),
    "%h": gettext_lazy("%h"),
    "%p": gettext_lazy("%p"),
    "%M": gettext_lazy("%M"),
    "%S": gettext_lazy("%S"),
}


def translate_date_format(format_string):
    """
    Translates a date/time format string (strftime) into a description
    in the current locale.
    """
    translated_parts = []
    i = 0
    while i < len(format_string):
        if format_string[i] == "%":
            if i + 1 < len(format_string):
                code = format_string[i : i + 2]
                # Handle the double percentage '%%' which means a literal '%'.
                if code == "%%":
                    translated_parts.append("%")
                elif code in FORMAT_CODE_DESCRIPTIONS:
                    # Add translated description
                    translated_parts.append(str(FORMAT_CODE_DESCRIPTIONS[code]))
                else:
                    # If the code is not in our dictionary, add it as is
                    translated_parts.append(code)
                i += 2
            else:
                # A single '%' at the end of the string
                translated_parts.append("%")
                i += 1
        else:
            # Add literal characters as is
            translated_parts.append(format_string[i])
            i += 1

    return "".join(translated_parts)


def create_thumbnail(image: models.ImageField, size: int) -> InMemoryUploadedFile:
    """
    Creates a thumbnail for a photo.

    If the photo is larger than settings.GALLERIES_THUMBNAIL_SIZE, it is resized
    to that size and saved as a new file. Otherwise, the original photo is used
    as the thumbnail.

    :param image: The image to create a thumbnail for.
    :param size: The requested size of the thumbnail. If the image is larger
        than this, it is resized.
    :return: An InMemoryUploadedFile representing the thumbnail.
    """
    if image.height <= size or image.width <= size:
        return image

    output_thumb = BytesIO()
    filename = image.name.split("/")[-1]
    file, ext = os.path.splitext(filename)
    # ISSUE WITH Image.open() which raises "ValueError: seek on closed file" in some circumstances
    if image.file.closed:
        image.file = default_storage.open(image.name, "rb")
    with Image.open(image.file) as img:
        img.thumbnail((size, size))
        img = ImageOps.exif_transpose(img)  # avoid image rotating
        # use WEBP format for thumbnails instead of JPEG to avoid loss of transparency
        img.save(output_thumb, format="WEBP", quality=90)
        size = sys.getsizeof(output_thumb)
        thumbnail = InMemoryUploadedFile(
            output_thumb, "ImageField", f"{file}.webp", "image/webp", size, None
        )
        logger.debug(f"Resized and saved thumbnail for {image.name}, size={size}")
        return thumbnail


def protected_media_url(media):
    media = str(media)
    # print("media=", media, "settings.MEDIA_ROOT=", settings.MEDIA_ROOT)
    if media.startswith(str(settings.MEDIA_ROOT)):
        media = media[len(str(settings.MEDIA_ROOT)) + 1 :]
    else:
        # for a file in base_dir/media when MEDIA_ROOT has been changed
        p = str(settings.BASE_DIR / settings.MEDIA_REL)
        if media.startswith(p):
            media = media[len(p) + 1 :]
    return reverse("get_protected_media", args=[quote(media)])


def check_edit_permission(request, owner):
    if request.user.is_superuser or owner.id == request.user.id:
        return True
    raise PermissionDenied(_("You do not have permission to edit/delete this object."))


def _fs_rmtree(storage, prefix):
    if isinstance(storage, FileSystemStorage):  # special case for FileSystemstorage1
        path = settings.MEDIA_ROOT / prefix
        if os.path.isdir(path):
            shutil.rmtree(path)
        return True
    return False


def _rm_emty_folders(storage, folder_stack):
    # delete empty folders
    while folder_stack:
        path = folder_stack.pop()
        try:
            storage.delete(path)
        except Exception:
            pass


def _recursive_rmtree(storage, prefix):
    stack = [prefix]
    dstack = [prefix]
    while stack:
        path = stack.pop()
        try:
            dirs, files = storage.listdir(path)
        except NotImplementedError:
            break
        # delete files
        for f in files:
            name = f"{path}/{f}"
            try:
                storage.delete(name)
            except Exception:
                pass
        # stack subfolders
        for d in dirs:
            stack.append(f"{path}/{d}")
            dstack.append(f"{path}/{d}")

    _rm_emty_folders(storage, dstack)
    return


def storage_rmtree(storage, prefix):
    """
    Tries to delete all objects under `prefix` as well as `prefix` itself for a given Storage. prefix is a posix path
    - storage: an instance of Storage (or subclass)
    - prefix: path related to MEDIA_ROOT without leading slash (e.g. "clients/client_42")
    """
    if _fs_rmtree(storage, prefix):
        return

    prefix = str(prefix).strip("/")
    # Generic attempt: list recursively via listdir if available
    if hasattr(storage, "listdir"):
        _recursive_rmtree(storage, prefix)
        return

    # If listdir not available (e.g. some backends), try direct deletion of prefix
    logger.warning(
        f"listdir not available for {storage} - trying to delete {prefix} directly"
    )
    storage.delete(f"{prefix}/")
