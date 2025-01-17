from django.db.models import Count
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.views.generic import (
    CreateView, DetailView, ListView, UpdateView, DeleteView)

from .models import Post, Category, PostComment
from .forms import PostForm, PostCommentForm

LIMIT_OF_POST = 10
User = get_user_model()


def get_post_list(queryset):
    current_time = timezone.now()
    filters = {
        'pub_date__lte': current_time,
        'is_published': True,
        'category__is_published': True
    }

    return queryset.select_related(
        'location', 'category', 'author'
    ).filter(
        **filters
    ).annotate(comment_count=Count('comments'))


def get_paginator(request, post_list):
    page_number = request.GET.get('page')
    paginator = Paginator(post_list, LIMIT_OF_POST)
    page_obj = paginator.get_page(page_number)

    return page_obj


class CategoryListView(ListView):
    template_name = 'blog/category.html'
    paginate_by = LIMIT_OF_POST

    ordering = '-pub_date'

    def get_queryset(self):
        self.category = Category.objects.only(
            'title', 'description'
        ).filter(
            slug=self.kwargs.get('category_slug'), is_published=True).get()

        self.queryset = get_post_list(Post.objects.filter(
            category=self.category.id))
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class PostCreateView(CreateView):
    template_name = 'blog/create.html'
    model = Post
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:profile', kwargs={'username': self.request.user})


class PostUpdateView(UpdateView):
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'
    model = Post
    form_class = PostForm

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'post_id': self.kwargs.get('post_id')})


class PostDeleteView(DeleteView):
    model = Post
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.get_object())
        return context


class PostListView(ListView):
    queryset = get_post_list(Post.objects.all())
    template_name = 'blog/index.html'
    paginate_by = LIMIT_OF_POST
    ordering = '-pub_date'


class PostDetailView(DetailView):
    template_name = 'blog/detail.html'
    queryset = get_post_list(Post.objects.all())
    pk_url_kwarg = 'post_id'

    def get_form(self):
        return PostCommentForm()

    def get_comments(self):
        return self.object.comments.select_related(
            'author'
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "comments": self.get_comments(),
            "form": self.get_form(),
        })
        return context


class CommentCreateView(CreateView):
    http_method_names = ['post']
    model = PostComment
    form_class = PostCommentForm

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail', kwargs={'post_id': self.kwargs.get('post_id')}
        )

    def form_valid(self, form):
        post_id = self.kwargs.get('post_id')
        post = get_object_or_404(Post, pk=post_id)
        form.instance.author = self.request.user
        form.instance.post = post
        return super().form_valid(form)


class CommentUpdateView(UpdateView):
    model = PostComment
    form_class = PostCommentForm
    template_name = 'blog/comment.html'
    context_object_name = 'comment'

    def get_object(self, queryset=None):
        post_comments = get_object_or_404(
            Post, pk=self.kwargs.get('post_id')).comments.all()
        obj = get_object_or_404(
            post_comments, pk=self.kwargs.get('comment_id'))
        return obj

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail', kwargs={'post_id': self.kwargs.get('post_id')}
        )


class CommentDeleteView(DeleteView):
    model = PostComment
    form_class = PostCommentForm
    template_name = 'blog/comment.html'
    context_object_name = 'comment'

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail', kwargs={'post_id': self.kwargs.get('post_id')}
        )

    def get_object(self, queryset=None):
        queryset = get_object_or_404(
            Post, pk=self.kwargs.get('post_id')
        ).comments.all()
        comment_id = self.kwargs.get('comment_id')
        return get_object_or_404(queryset, pk=comment_id)


class ProfileDetailView(DetailView):
    template_name = 'blog/profile.html'
    context_object_name = 'profile'
    slug_url_kwarg = 'username'
    slug_field = 'username'
    model = User

    def get_post(self):
        # user = User.objects.only('id').filter(username=self.kwargs.get('username'))
        queryset = self.object.posts.all().order_by('-pub_date')
        return get_post_list(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_obj'] = get_paginator(self.request, self.get_post())
        return context


class ProfileUpdateView(UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'username', 'email']
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        obj = get_object_or_404(User, username=self.request.user)
        return obj

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile', kwargs={'username': self.request.user}
        )
