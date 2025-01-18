from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Post, PostComment
from .forms import PostCommentForm


class PostActionMixin(LoginRequiredMixin):
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    model = Post

    def dispatch(self, request, *args, **kwargs):
        object = self.get_object()
        if object.author != request.user and not request.user.is_superuser:
            return HttpResponseRedirect(
                reverse('blog:post_detail',
                        kwargs={'post_id': self.kwargs.get('post_id')}))
        return super().dispatch(request, *args, **kwargs)


class CommentActionMixin(LoginRequiredMixin):
    model = PostComment
    form_class = PostCommentForm
    template_name = 'blog/comment.html'
    context_object_name = 'comment'

    def dispatch(self, request, *args, **kwargs):
        object = self.get_object()
        if object.author != request.user and not request.user.is_superuser:
            return HttpResponseRedirect(
                reverse('blog:post_detail',
                        kwargs={'post_id': self.kwargs.get('post_id')}))
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.kwargs.get('post_id')})
