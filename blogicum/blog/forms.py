from django import forms

from .models import Post, PostComment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ['author', 'is_published']
        widgets = {
            'pub_date': forms.DateTimeInput(attrs={'type': 'datetime-local'})
        }


class PostCommentForm(forms.ModelForm):
    class Meta:
        model = PostComment
        fields = ('text',)
