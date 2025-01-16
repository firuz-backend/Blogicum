from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Post, Category

LIMIT_OF_POST = 5


def get_post_list():
    current_time = timezone.now()
    filters = {
        'pub_date__lte': current_time,
        'is_published': True,
        'category__is_published': True
    }

    return Post.objects.select_related(
        'location', 'category', 'author'
    ).filter(
        **filters
    )


def index(request):
    template = 'blog/index.html'
    post_list = get_post_list()[:LIMIT_OF_POST]
    context = {'post_list': post_list}
    return render(request, template, context)


def post_detail(request, post_id: int):
    template = 'blog/detail.html'
    post = get_object_or_404(get_post_list(), pk=post_id)

    context = {'post': post}
    return render(request, template, context)


def category_posts(request, category_slug: str):
    template = 'blog/category.html'

    category = get_object_or_404(
        Category.objects.only(
            'title', 'description'
        ).filter(slug=category_slug, is_published=True)
    )

    post_list = get_post_list().filter(category=category)

    context = {
        'post_list': post_list,
        'category': category
    }
    return render(request, template, context)
