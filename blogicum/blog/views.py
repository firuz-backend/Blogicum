from django.http import HttpResponseRedirect, Http404
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.views.generic import (
    CreateView, DetailView, ListView, UpdateView, DeleteView)

from .models import Post, Category, PostComment
from .forms import PostForm, PostCommentForm

LIMIT_OF_POST = 10
User = get_user_model()
FILTERS = {
    'is_published': True,
    'category__is_published': True
}


def get_post_list():

    return Post.objects.select_related(
        'location', 'category', 'author'
    ).annotate(comment_count=Count('comments'))


def get_paginator(request, post_list):
    page_number = request.GET.get('page')
    paginator = Paginator(post_list, LIMIT_OF_POST)
    page_obj = paginator.get_page(page_number)

    return page_obj


class PostCreateView(LoginRequiredMixin, CreateView):
    template_name = 'blog/create.html'
    model = Post
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:profile',
                            kwargs={'username': self.request.user})


class PostActionMixin(LoginRequiredMixin):
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    model = Post

    def dispatch(self, request, *args, **kwargs):
        object = self.get_object()
        if object.author != request.user and not request.user.is_superuser:
            return HttpResponseRedirect(
                reverse_lazy('blog:post_detail',
                             kwargs={'post_id': self.kwargs.get('post_id')}))
        return super().dispatch(request, *args, **kwargs)


class PostUpdateView(PostActionMixin, UpdateView):
    form_class = PostForm

    def get_success_url(self):
        return reverse_lazy('blog:post_detail',
                            kwargs={'post_id': self.kwargs.get('post_id')})


class PostDeleteView(PostActionMixin, DeleteView):
    success_url = reverse_lazy('blog:index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.get_object())
        return context


class PostListView(ListView):
    queryset = get_post_list().filter(**FILTERS, pub_date__lte=timezone.now())
    template_name = 'blog/index.html'
    paginate_by = LIMIT_OF_POST
    ordering = '-pub_date'


class PostDetailView(DetailView):
    template_name = 'blog/detail.html'
    queryset = get_post_list()
    model = Post
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if not post.is_published and post.author != request.user:
            raise Http404
        if not post.category.is_published and post.author != request.user:
            raise Http404
        if post.pub_date > timezone.now() and post.author != request.user:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_form(self):
        return PostCommentForm()

    def get_comments(self):
        return self.object.comments.select_related(
            'author'
        ).order_by('created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "comments": self.get_comments(),
            "form": self.get_form(),
        })
        return context


class CommentCreateView(LoginRequiredMixin, CreateView):
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


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = PostComment
    form_class = PostCommentForm
    template_name = 'blog/comment.html'
    context_object_name = 'comment'

    def dispatch(self, request, *args, **kwargs):
        object = self.get_object()
        if object.author != request.user and not request.user.is_superuser:
            return HttpResponseRedirect(
                reverse_lazy('blog:post_detail',
                             kwargs={'post_id': self.kwargs.get('post_id')}))
        return super().dispatch(request, *args, **kwargs)

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


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = PostComment
    form_class = PostCommentForm
    template_name = 'blog/comment.html'
    context_object_name = 'comment'

    def dispatch(self, request, *args, **kwargs):
        object = self.get_object()
        if object.author != request.user and not request.user.is_superuser:
            return HttpResponseRedirect(
                reverse_lazy('blog:post_detail',
                             kwargs={'post_id': self.kwargs.get('post_id')}))
        return super().dispatch(request, *args, **kwargs)

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

    def profile_post_list(self, queryset):
        return queryset.select_related(
            'location', 'category', 'author'
        ).annotate(comment_count=Count('comments'))

    def get_post(self):
        queryset = self.object.posts.all().order_by('-pub_date')
        if self.request.user == self.object:
            return self.profile_post_list(queryset)

        return self.profile_post_list(queryset).filter(**FILTERS)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_obj'] = get_paginator(self.request, self.get_post())
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
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


class CategoryListView(ListView):
    template_name = 'blog/category.html'
    paginate_by = LIMIT_OF_POST

    def dispatch(self, request, *args, **kwargs):
        self.category = get_object_or_404(
            Category, slug=self.kwargs.get('category_slug'))
        if not self.category.is_published:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = self.category.posts.filter(
            is_published=True,
            pub_date__lte=timezone.now()).order_by('-pub_date')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context
