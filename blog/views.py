# Create your views here.

from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from blog.forms import PostForm, CommentForm
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from blog.models import Post, Comment
from django.shortcuts import render
from django.contrib.auth import authenticate, logout
from django.contrib.auth import login as auth_login


class AboutView(TemplateView):
    template_name = 'about.html'

    def get_context_data(self, **kwargs):
        all_categories = set(Post.objects.values_list('category', flat=True))
        all_categories = [x.lower() for x in list(all_categories)]
        all_categories = set(sorted(all_categories))
        context = super().get_context_data(**kwargs)
        context["categories"] = all_categories
        return context


class PostListView(ListView):
    template_name = 'post_list.html'
    model = Post

    def get_queryset(self):
        return Post.objects.filter(published_date__lte=timezone.now()).order_by('-published_date')

    def get_context_data(self, **kwargs):
        all_categories = set(Post.objects.values_list('category', flat=True))
        all_categories = [x.lower() for x in list(all_categories)]
        all_categories = set(sorted(all_categories))
        context = super().get_context_data(**kwargs)
        context["categories"] = all_categories
        return context


class PostDetailView(DetailView):
    template_name = 'post_detail.html'
    model = Post


class CreatePostView(CreateView, LoginRequiredMixin):
    login_url = '/login/'
    redirect_field_name = 'post_detail.html'
    template_name = 'post_form.html'
    form_class = PostForm

    model = Post


class PostUpdateView(LoginRequiredMixin, UpdateView):
    login_url = '/login/'
    redirect_field_name = 'post_detail.html'
    template_name = 'post_form.html'
    form_class = PostForm

    model = Post


class PostDeleteView(LoginRequiredMixin, DeleteView):
    template_name = 'post_confirm_delete.html'
    model = Post
    success_url = reverse_lazy('post_list')


class DraftListView(LoginRequiredMixin, ListView):
    login_url = '/login/'
    template_name = 'post_draft_list.html'
    redirect_field_name = 'post_list.html'
    model = Post

    def get_queryset(self):
        return Post.objects.filter(published_date__isnull=True).order_by('create_date')


######################################################################################################

@login_required
def post_publish(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.publish()
    return redirect('post_detail', pk=pk)


@login_required
def add_comment_to_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.save()
            return redirect('post_detail', pk=post.pk)

    else:
        form = CommentForm()

    return render(request, 'commentform.html', {'form': form})


@ login_required
def comment_approve(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.approve()
    return redirect('post_detail', pk=comment.post.pk)


@ login_required
def comment_remove(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    post_pk = comment.post.pk
    comment.delete()
    return redirect('post_detail', pk=post_pk)


def login(request):
    if request.method == 'POST':
        username = (request.POST.get('username'))
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('post_list')

    form = CommentForm()

    return render(request, 'login.html', {'form': form})


@ login_required(login_url='/login')
def user_logout(request):
    logout(request)
    return render(request, 'login.html')


def search(request):
    if request.method == 'POST':
        search_term = request.POST.get('search')
        totalcount = Post.objects.count()
        allposts = Post.objects.filter(text__contains=search_term).values()

        context = {'total': totalcount,
                   'allposts': allposts, 'search': search_term}
        return render(request, 'search.html', context=context)


def category(request, category):
    all_categories = set(Post.objects.values_list('category', flat=True))
    all_categories = [x.lower() for x in list(all_categories)]
    all_categories = set(sorted(all_categories))
    totalcount = Post.objects.count()
    allposts = Post.objects.filter(category=category).values()
    context = {'total': totalcount, 'allposts': allposts,
               'category': category, 'categories': all_categories}
    return render(request, 'category.html', context=context)


def author(request, id):
    totalcount = Post.objects.count()
    allposts = Post.objects.filter(author_id=id).values()
    context = {'total': totalcount, 'allposts': allposts, 'category': category}
    return render(request, 'author.html', context=context)
