from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class AboutPagesTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_about_pages(self):
        """Тестирование доступности страниц /about/"""
        template_urls = {
            "about:author": 200,
            "about:tech": 200
        }
        for template, code in template_urls.items():
            with self.subTest(code=code):
                response = self.client.get(reverse(template))
                self.assertEqual(response.status_code, code)

    def test_about_pages_views_use_correct_templates(self):
        """Тестирование использования view-функциями корректных шаблонов"""
        templates_pages_names = {
            "author.html": reverse("about:author"),
            "tech.html": reverse("about:tech"),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertTemplateUsed(response, template)
