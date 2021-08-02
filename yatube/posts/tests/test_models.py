from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="тест группа",
            slug="test",
            description="тестовое описание"
        )

    def test_str_group(self):
        """Тестирование метода __str__ Group"""
        group = GroupModelTest.group
        self.assertEqual(group.title, str(group))


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="testname")
        cls.post = Post.objects.create(
            text="тестовый текст",
            author=PostModelTest.user
        )

    def test_str_post(self):
        """Тестирование метода __str__ Post"""
        post = PostModelTest.post
        expected_value = post.text[:15]
        self.assertEqual(expected_value, str(post))
