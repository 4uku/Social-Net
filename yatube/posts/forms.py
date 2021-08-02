from django import forms
from django.forms.widgets import Textarea

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("text", "group", "image")
        labels = {
            "text": "Текст",
            "group": "Группа",
            "image": "Изображение",
        }
        help_texts = {
            "text": "Введите текст поста",
            "group": "Выберите группу",
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)
        widgets = {
            "text": Textarea(attrs={"class": "forms-control"}),
        }
