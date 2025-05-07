from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.core.paginator import Paginator
from django.db import transaction
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
import random


from post.models import Post, Follow, Stream
from django.contrib.auth.models import User
from authy.models import Profile
from .forms import EditProfileForm, UserRegisterForm
from django.urls import resolve
from comment.models import Comment

def UserProfile(request, username):
    Profile.objects.get_or_create(user=request.user)
    user = get_object_or_404(User, username=username)
    profile = Profile.objects.get(user=user)
    url_name = resolve(request.path).url_name
    posts = Post.objects.filter(user=user).order_by('-posted')

    if url_name == 'profile':
        posts = Post.objects.filter(user=user).order_by('-posted')
    else:
        posts = profile.favourite.all()
    
    # Profile Stats
    posts_count = Post.objects.filter(user=user).count()
    following_count = Follow.objects.filter(follower=user).count()
    followers_count = Follow.objects.filter(following=user).count()
    # count_comment = Comment.objects.filter(post=posts).count()
    follow_status = Follow.objects.filter(following=user, follower=request.user).exists()

    # pagination
    paginator = Paginator(posts, 8)
    page_number = request.GET.get('page')
    posts_paginator = paginator.get_page(page_number)

    context = {
        'posts': posts,
        'profile':profile,
        'posts_count':posts_count,
        'following_count':following_count,
        'followers_count':followers_count,
        'posts_paginator':posts_paginator,
        'follow_status':follow_status,
        # 'count_comment':count_comment,
    }
    return render(request, 'profile.html', context)
    

# def EditProfile(request):
#     user = request.user.id
#     profile = Profile.objects.get(user__id=user)

#     if request.method == "POST":
#         form = EditProfileForm(request.POST, request.FILES, instance=request.user.profile)
#         if form.is_valid():
#             profile.image = form.cleaned_data.get('image')
#             profile.first_name = form.cleaned_data.get('first_name')
#             profile.last_name = form.cleaned_data.get('last_name')
#             profile.location = form.cleaned_data.get('location')
#             profile.url = form.cleaned_data.get('url')
#             profile.bio = form.cleaned_data.get('bio')
#             profile.save()
#             return redirect('profile', profile.user.username)
#     else:
#         form = EditProfileForm(instance=request.user.profile)

#     context = {
#         'form':form,
#     }
#     return render(request, 'editprofile.html', context)

from django.shortcuts import render, redirect
from .forms import EditProfileForm
from .models import Profile

def EditProfile(request):
    user = request.user  # Get the current logged-in user
    profile = Profile.objects.get(user=user)  # Get the profile associated with the user

    if request.method == "POST":
        form = EditProfileForm(request.POST, request.FILES, instance=profile)  # Bind the form to the profile instance
        if form.is_valid():
            # Update user fields (first_name, last_name)
            user.first_name = form.cleaned_data.get('first_name')
            user.last_name = form.cleaned_data.get('last_name')
            user.save()  # Save the user model instance

            # Update profile fields
            profile.image = form.cleaned_data.get('image')
            profile.location = form.cleaned_data.get('location')
            profile.url = form.cleaned_data.get('url')
            profile.bio = form.cleaned_data.get('bio')
            profile.save()  # Save the profile model instance

            return redirect('profile', profile.user.username)  # Redirect to the updated profile page

    else:
        form = EditProfileForm(instance=profile)  # Prepopulate the form with the current profile data

    context = {
        'form': form,
    }
    return render(request, 'editprofile.html', context)


def follow(request, username, option):
    user = request.user
    following = get_object_or_404(User, username=username)

    try:
        f, created = Follow.objects.get_or_create(follower=request.user, following=following)

        if int(option) == 0:
            f.delete()
            Stream.objects.filter(following=following, user=request.user).all().delete()
        else:
            posts = Post.objects.all().filter(user=following)[:25]
            with transaction.atomic():
                for post in posts:
                    stream = Stream(post=post, user=request.user, date=post.posted, following=following)
                    stream.save()
        return HttpResponseRedirect(reverse('profile', args=[username]))

    except User.DoesNotExist:
        return HttpResponseRedirect(reverse('profile', args=[username]))


# def register(request):
#     if request.method == "POST":
#         form = UserRegisterForm(request.POST)
#         if form.is_valid():
#             new_user = form.save()
#             # Profile.get_or_create(user=request.user)
#             username = form.cleaned_data.get('username')
#             messages.success(request, f'Hurray your account was created!!')

#             # Automatically Log In The User
#             new_user = authenticate(username=form.cleaned_data['username'],
#                                     password=form.cleaned_data['password1'],)
#             login(request, new_user)
#             # return redirect('editprofile')
#             return redirect('index')
            


#     # elif request.user.is_authenticated:
#     #     return redirect('index')
#     else:
#         form = UserRegisterForm()
#     context = {
#         'form': form,
#     }
#     return render(request, 'sign-up.html', context)

def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            print("Form is valid!")  # Debugging line to check if the form is valid
            new_user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Hurray your account was created!!')

            # Authenticate the user
            new_user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password1'])
            print(f"Attempting to authenticate: {form.cleaned_data['username']}, Password: {form.cleaned_data['password1']}")  # Debugging line for username and password
            if new_user is not None:
                login(request, new_user)  # Log the user in if authentication is successful
                print(f"User logged in: {request.user.is_authenticated}")  # Check if the user is logged in
                return redirect('index')
            else:
                print("Authentication failed!")  # Log the error if authentication fails
                messages.error(request, "There was an error during authentication.")  # Show error message
        else:
            print("Form is not valid!")  # Debugging line if the form is not valid
            print(form.errors)  # Print form validation errors to help debug

    else:
        form = UserRegisterForm()

    context = {
        'form': form,
    }
    return render(request, 'sign-up.html', context)

# Store OTPs temporarily
otp_storage = {}

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST['email']
        try:
            user = User.objects.get(email=email)
            otp = random.randint(100000, 999999)
            otp_storage[email] = otp  # You could use cache/db in production

            send_mail(
                'Your OTP for Password Reset',
                f'Hello {user.username}, your OTP is {otp}',
                'your_email@gmail.com',
                [email],
                fail_silently=False,
            )
            request.session['email'] = email
            return redirect('verify-otp')
        except User.DoesNotExist:
            messages.error(request, 'User with this email does not exist.')
    return render(request, 'forgot_password.html')


def verify_otp(request):
    if request.method == 'POST':
        email = request.session.get('email')
        entered_otp = request.POST['otp']
        if email and otp_storage.get(email) == int(entered_otp):
            return redirect('reset-password')
        else:
            messages.error(request, 'Invalid OTP.')
    return render(request, 'verify_otp.html')


def reset_password(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm = request.POST['confirm']
        email = request.session.get('email')
        if password == confirm and email:
            user = User.objects.get(email=email)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password reset successful.')
            return redirect('sign-in')
        else:
            messages.error(request, 'Passwords do not match.')
    return render(request, 'reset_password.html')

@login_required
def delete_profile(request):
    user = request.user
    user.delete()  # This will delete the user and their profile due to CASCADE
    messages.success(request, "Your profile has been deleted.")
    return redirect('sign-in')  # Redirect to login or homepage


