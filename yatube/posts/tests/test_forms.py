import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.user = User.objects.create_user(username="testname")
        cls.group = Group.objects.create(
            title="тест группа",
            slug="test",
            description="тестовое описание"
        )
        cls.post = Post.objects.create(
            text="text for change",
            author=cls.user,
            group=cls.group
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authoriized_client = Client()
        self.authoriized_client.force_login(PostFormTest.user)

    def test_new_post_create(self):
        """Тестирование формы создания поста"""
        post_count = Post.objects.count()
        post_data = {
            "text": "test text",
            "author": PostFormTest.user,
            "group": PostFormTest.group.id,
            "image": self.uploaded
        }
        self.authoriized_client.post(
            reverse("new_post"), data=post_data, follow=True
        )
        first_query_set = Post.objects.first()
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(first_query_set.text, post_data["text"])
        self.assertEqual(first_query_set.group, PostFormTest.group)
        self.assertEqual(first_query_set.author, PostFormTest.user)

    def test_post_edit_saving_changes(self):
        """Тестирование формы редактирования поста"""
        post_data = {
            "text": "test text"
        }
        response = self.authoriized_client.post(
            reverse("post_edit",
                    kwargs={"username": PostFormTest.user.username,
                            "post_id": PostFormTest.post.id}),
            data=post_data, follow=True
        )
        PostFormTest.post.refresh_from_db()
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(Post.objects.first().text, post_data["text"])
        self.assertRedirects(
            response,
            reverse("post", kwargs={"username": PostFormTest.user.username,
                                    "post_id": PostFormTest.post.id}),
            302,
            200
        )

    def test_anonymouse_cant_create_a_post(self):
        """Тестирование недоступности формы для анонима"""
        self.guest = Client()
        post_count = Post.objects.count()
        response = self.guest.post(
            reverse("new_post"), data={"text": "test text"}, follow=True
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertRedirects(
            response,
            (reverse("login") + "?next=" + reverse("new_post")),
            302,
            200
        )
