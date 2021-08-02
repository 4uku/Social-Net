from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="testname")
        cls.viewer = User.objects.create_user(username="testname2")
        cls.group = Group.objects.create(
            title="тест группа",
            slug="test",
            description="тестовое описание"
        )
        cls.post = Post.objects.create(
            text="test text",
            author=cls.user
        )

    def setUp(self):
        self.guest_client = Client()
        self.authoriized_client = Client()
        self.authoriized_client.force_login(self.user)
        self.viewer_client = Client()
        self.viewer_client.force_login(self.viewer)
        self.urls = {
            "homepage": "/",
            "group_page": f"/group/{self.group.slug}/",
            "new_page": "/new/",
            "profile_page": f"/{self.user.username}/",
            "post_view_page": f"/{self.user.username}/{self.post.id}/",
            "post_edit_page": f"/{self.user.username}/{self.post.id}/edit/",
        }

    def test_pages_for_anonymouse(self):
        """Тестирование доступности страниц"""
        all_variants = [
            (self.urls["homepage"], 200, self.guest_client),
            (self.urls["group_page"], 200, self.guest_client),
            (self.urls["new_page"], 302, self.guest_client),
            (self.urls["profile_page"], 200, self.guest_client),
            (self.urls["post_view_page"], 200, self.guest_client),
            (self.urls["post_edit_page"], 302, self.guest_client),
            (self.urls["new_page"], 200, self.authoriized_client),
            (self.urls["post_edit_page"], 200, self.authoriized_client),
            (self.urls["post_edit_page"], 302, self.viewer_client)
        ]
        for item in all_variants:
            url = item[0]
            code = item[1]
            client = item[2]
            with self.subTest(url=url):
                response = client.get(url)
                self.assertEqual(response.status_code, code)

    def test_urls_uses_correct_templates(self):
        """Тестирование использования корректных шаблонов"""
        templates_url_names = {
            "index.html": self.urls["homepage"],
            "group.html": self.urls["group_page"],
            "new_post.html": self.urls["new_page"],
        }
        for template, adress in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authoriized_client.get(adress)
                self.assertTemplateUsed(response, template)
        response = self.authoriized_client.get(self.urls["post_edit_page"])
        self.assertTemplateUsed(response, "new_post.html")
