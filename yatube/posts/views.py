from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post

User = get_user_model()


def paginator(request, post_list):
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return page


@cache_page(20, key_prefix="index_page")
def index(request):
    post_list = Post.objects.all()
    page = paginator(request, post_list)
    return render(request, "index.html", {"page": page})


@login_required
def follow_index(request):
    user_follower = request.user.follower.all()
    authors_list = []
    for follow in user_follower:
        authors_list.append(follow.author)
    post_list = Post.objects.all().filter(author__in=authors_list)
    page = paginator(request, post_list)
    return render(request, "follow.html", {"page": page, })


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if ((request.user != author)
       and not Follow.objects.filter(author=author,
                                     user=request.user).exists()):
        Follow.objects.create(author_id=author.id, user_id=request.user.id)
    return redirect("profile", username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    author_following = author.following.get(user=request.user)
    if ((request.user != author)
       and Follow.objects.filter(author=author, user=request.user).exists()):
        author_following.delete()
    return redirect("profile", username)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page = paginator(request, post_list)
    return render(request, "group.html", {"page": page,
                                          "group": group})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    posts_count = post_list.count()
    page = paginator(request, post_list)
    following = None
    if author.following.filter(user=request.user):
        following = True
    else:
        following = False
    return render(request, "profile.html", {"author": author,
                                            "count": posts_count,
                                            "page": page,
                                            "following": following,
                                            })


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    posts_count = post.author.posts.count()
    comment_button = False
    return render(request, "post.html", {"author": post.author,
                                         "post": post,
                                         "count": posts_count,
                                         "form": form,
                                         "comments": comments,
                                         "comment_button": comment_button,
                                         })


@login_required
@csrf_exempt
def new_post(request):
    header = "Добавить запись"
    button = "Добавить"
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("index")
    return render(request, "new_post.html", {"form": form,
                                             "header": header,
                                             "button": button})


@login_required
@csrf_exempt
def post_edit(request, username, post_id):
    header = "Редактировать запись"
    button = "Сохранить"
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect("post", username=username, post_id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        post.save()
        return redirect("post", username=post.author, post_id=post.id)
    return render(request, "new_post.html", {"form": form,
                                             "header": header,
                                             "button": button})


@login_required
@csrf_exempt
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect("post", username, post_id)
    return render(request, "includes/comments.html", {"form": form})


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
