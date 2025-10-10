from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegisterForm, ProfileForm

def register_user(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect("userprofile:login")
    else:
        form = RegisterForm()
    return render(request, "userprofile/register.html", {"form": form})


def login_user(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("userprofile:profile")  # redirect ke halaman profile
    else:
        form = AuthenticationForm()
    return render(request, "userprofile/login.html", {"form": form})


def logout_user(request):
    logout(request)
    return redirect("userprofile:login")


def profile_user(request):
    if not request.user.is_authenticated:
        return redirect("userprofile:login")  # kalau belum login

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("userprofile:profile")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "userprofile/profile.html", {"form": form})
