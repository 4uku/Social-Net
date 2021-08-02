import shutil
import tempfile
from yatube.posts.models import Follow

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PagesTest(TestCase):
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
        cls.group2 = Group.objects.create(
            title="тест группа2",
            slug="test2",
            description="тестовое описание"
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
        cls.post = Post.objects.create(
            text="test text",
            group=cls.group,
            author=cls.user,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authoriized_client = Client()
        self.authoriized_client.force_login(self.user)
        cache.clear()

    def test_pages_use_correct_templates(self):
        """Тестирование испольвания view-функциями шаблонов"""
        templates_pages_names = {
            "index.html": reverse("index"),
            "group.html": reverse("group",
                                  kwargs={"slug": self.group.slug}),
            "new_post.html": reverse("new_post"),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authoriized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_homepage_use_correct_context(self):
        """Тестирование контекста index, group, profile"""
        response_index = self.authoriized_client.get(reverse("index"))
        response_group = self.authoriized_client.get(
            reverse("group", kwargs={"slug": self.group.slug})
        )
        response_profile = self.authoriized_client.get(
            reverse("profile", kwargs={"username": self.user.username})
        )

        def context(self, response):
            first_object = response.context.get("page").object_list[0]
            first_post_text = first_object.text
            first_post_group = first_object.group
            first_post_author = first_object.author
            first_post_image = first_object.image
            self.assertEqual(first_post_text, self.post.text)
            self.assertEqual(first_post_group, self.post.group)
            self.assertEqual(first_post_author, self.post.author)
            self.assertEqual(first_post_image, self.post.image)

        context(self, response_index)
        context(self, response_group)
        context(self, response_profile)

    def test_new_post_and_edit_post_use_correct_context(self):
        """Тестирование контекста страницы /new/ и /edit/"""
        response_new = self.authoriized_client.get(reverse("new_post"))
        response_edit = self.authoriized_client.get(
            reverse("post_edit", kwargs={"username": self.user.username,
                                         "post_id": self.post.id}))

        def test(self, response):
            form_fields = {
                "text": forms.fields.CharField,
                "group": forms.fields.ChoiceField,
                "image": forms.fields.ImageField,
            }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context["form"].fields[value]
                    self.assertIsInstance(form_field, expected)

        test(self, response_new)
        test(self, response_edit)

    def test_post_page_use_correct_context(self):
        """Тестирование контекста страницы поста"""
        response = self.authoriized_client.get(
            reverse("post", kwargs={"username": self.user.username,
                                    "post_id": self.post.id})
        )
        self.assertEqual(response.context["post"].text, self.post.text)
        self.assertEqual(response.context["post"].group.title,
                         self.post.group.title)
        self.assertEqual(response.context["author"], self.post.author)
        self.assertEqual(response.context["post"].image, self.post.image)

    def test_post_on_homepage(self):
        """Тестирование наличия поста с группой на главной странице"""
        response = self.authoriized_client.get(reverse("index"))
        first_object = response.context.get("page").object_list[0]
        self.assertEqual(first_object, self.post)

    def test_post_on_group_page(self):
        """Тестирование наличия поста на странице группы"""
        response = self.authoriized_client.get(
            reverse("group", kwargs={"slug": self.group.slug})
        )
        first_object = response.context.get("page").object_list[0]
        self.assertEqual(first_object, self.post)

    def test_post_not_in_wrong_group(self):
        """Тестирование отсутствия поста на странице другой группы"""
        response = self.authoriized_client.get(
            reverse("group", kwargs={"slug": self.group2.slug})
        )
        self.assertEqual(len(response.context["page"]), 0)

    def test_homepage_cache(self):
        """Тестирование кэша"""
        count_before_create = Post.objects.count()
        response = self.authoriized_client.get(reverse("index"))
        Post.objects.create(
            text="test cache",
            author=self.user
        )
        self.assertEqual(len(response.context["page"]), count_before_create)
        cache.clear()
        response = self.authoriized_client.get(reverse("index"))
        count_after_create = Post.objects.count()
        self.assertEqual(len(response.context["page"]), count_after_create)

    def test_dich(self):
        response = self.authoriized_client.get(reverse("index"))
        print(response.request)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="testname")
        cls.group = Group.objects.create(
            title="тест группа",
            slug="test",
            description="тестовое описание")
        for cls.post in range(15):
            cls.post = Post.objects.create(
                text="test text",
                author=cls.user,
                group=cls.group
            )

    def setUp(self):
        self.client = Client()

    def test_first_page_contains_ten_records(self):
        """Тестирование первой страницы паджинитора homepage"""
        response = self.client.get(reverse("index"))
        self.assertEqual(len(response.context["page"]), 10)

    def test_second_page_contains_five_records(self):
        """Тестирование второй страницы паджинатора homepage"""
        response = self.client.get(reverse("index") + "?page=2")
        self.assertEqual(len(response.context["page"]), 5)

    def test_group_page_contains_ten_records(self):
        """Тестирование первой страницы паджинатора grouppage"""
        response = self.client.get(
            reverse("group", kwargs={"slug": self.group.slug})
        )
        self.assertEqual(len(response.context["page"]), 10)

    def test_profile_page_contains_ten_records(self):
        """Тестирова первой страницы паджинатора profile"""
        response = self.client.get(
            reverse("profile", kwargs={"username": self.user.username})
        )
        self.assertEqual(len(response.context["page"]), 10)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="user")
        cls.author = User.objects.create_user(username="author")
        cls.post = Post.objects.create(
            text="test text",
            author=cls.author
        )

    def setUp(self):
        super().setUp()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.guest_clien = Client()

    def test_authorized_user_can_follow(self):
        """Тестирование подписки для пользователя"""
        follows_count = Follow.objects.count()
        self.authorized_client.get(
            reverse("profile_follow",
                    kwargs={"username": self.author.username})
        )
        self.assertEqual(Follow.objects.count(), follows_count + 1)