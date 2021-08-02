from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class AboutPagesURLTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_about_pages_use_correct_templates(self):
        """Тестирование использования страницами корректных шаблонов"""
        templates_url_names = {
            "author.html": "/about/author/",
            "tech.html": "/about/tech/"
        }
        for template, adress in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.client.get(adress)
                self.assertTemplateUsed(response, template)
