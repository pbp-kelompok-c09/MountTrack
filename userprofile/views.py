from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, ProfileForm
from .models import UserProfile

def register_user(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect("userprofile:login")
    else:
        form = RegisterForm()
    return render(request, "register.html", {"form": form})


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
    return render(request, "login.html", {"form": form})


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
    return render(request, "profile.html", {"form": form})

@login_required(login_url='/login')
def admin_portal_user(request):
    if not request.user.is_staff:
        return redirect("userprofile:no_access")
    
    users = UserProfile.objects.all().order_by('username')

    if request.method == "POST":
        action = request.POST.get("action")

        # bagian add user
        if action == "add":
            username = request.POST.get("username")
            email = request.POST.get("email")
            password = request.POST.get("password")

            if username and password and email:
                UserProfile.objects.create_user(username=username, email=email, password=password)
            return redirect("userprofile:admin_portal")
        
        # bagian ubah status admin dan delete user
        user_id = request.POST.get("user_id")
        if user_id:
            target_user = UserProfile.objects.get(id=user_id)
            if target_user == request.user:
                return redirect("userprofile:admin_portal")

            # ubah status admin
            if action == "toggle":
                target_user.is_staff = not target_user.is_staff
                target_user.save()

            # delete user
            elif action == "delete":
                target_user.delete()

        return redirect("userprofile:admin_portal")

    return render(request, "admin_portal.html", {"users": users})

def no_access_user(request):
    return render(request, "no_access.html", status=403)
