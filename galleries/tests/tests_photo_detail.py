from datetime import date
from django.urls import reverse
from cm_main.utils import create_test_image, protected_media_url
from galleries.models import Photo, Gallery
from galleries.views.views_photo import PhotoDetailView
from .tests_utils import GalleryBaseTestCase
from .tests_gallery import get_gallery_name


class PhotoDetailTest(GalleryBaseTestCase):
    def setUp(self):
        super().setUp()
        # number of photos to create
        self.nb_photos = 4
        # position of the photo to display in the list of photos (starting from 0)
        # (supposed to be the same order as in the gallery)
        self.position = 2

        self.gallery = Gallery(name=get_gallery_name())
        self.gallery.save()
        self.photos = []
        for i in range(self.nb_photos):
            image = create_test_image(__file__, f"test-image-{i + 1}.jpg")
            p = Photo(
                name=f"photo #{i + 1}",
                gallery=self.gallery,
                date=date.today(),
                image=image,
            )
            p.save()
            self.photos.append(p)
        self.photo = self.photos[self.position]

    def test_photo_detail_with_pk(self):
        response = self.client.get(reverse("galleries:photo", args=[self.photo.id]))
        # print("pk: id:", self.photo.id, "position:", self.position, "max pos:", len(self.photos) - 1)
        self.assertEqual(response.status_code, 200)
        self.assertIs(response.resolver_match.func.view_class, PhotoDetailView)
        self.assertTemplateUsed(response, "galleries/photo_detail.html")
        self.assertContains(response, self.photo.name)
        self.assertContains(response, protected_media_url(self.photo.image.name))
        self.assertContains(
            response,
            f'data-next="{protected_media_url(self.photos[self.position + 1].image.name)}"',
        )
        self.assertContains(
            response,
            f'data-prev="{protected_media_url(self.photos[self.position - 1].image.name)}"',
        )

    def test_photo_detail_with_gallery_and_num(self):
        # print("gal&num: id:", self.photo.id, "position:", self.position, "max pos:", len(self.photos) - 1)
        response = self.client.get(
            reverse(
                "galleries:gallery_photo_url", args=[self.gallery.id, self.position + 1]
            ),
            **{"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 200)
        print("response:", response.json())
        self.assertEqual(
            response.json(),
            {
                "pk": self.photo.id,
                "image_url": protected_media_url(self.photo.image.name),
            },
        )
