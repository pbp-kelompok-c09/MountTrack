from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, ProfileForm
from .models import UserProfile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
import json


def register_user(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            # jadikan user dengan username "admin" sebagai admin
            if user.username == "admin":
                user.is_staff = True
                user.is_superuser = True

            user.save()
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
                nama_kosong = not getattr(user, "nama", None)
                telepon_kosong = not getattr(user, "nomor_telepon", None)
                umur_kosong = not getattr(user, "umur", None)

                if nama_kosong or telepon_kosong or umur_kosong:
                    return redirect("userprofile:my-profile")  # arahkan ke halaman profil untuk lengkapi data
                else:
                    return redirect("news:page_news") # lanjut ke news
    else:
        form = AuthenticationForm()
    return render(request, "login.html", {"form": form})

def logout_user(request):
    logout(request)
    return redirect("news:page_news")  # redirect ke halaman utama berita, diubah oleh ryan.


def profile_user(request):
    if not request.user.is_authenticated:
        return redirect("userprofile:login")  # kalau belum login

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            # dengan AJAX
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": True})
        else:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": False, "errors": form.errors}, status=400)
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "my_profile.html", {"form": form})

@login_required(login_url='/accounts/login')
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

@login_required(login_url='/accounts/login')
def get_users_json(request):
    if not request.user.is_staff:
        return JsonResponse({"error": "Forbidden"}, status=403)

    users = UserProfile.objects.all().values("id", "username", "email", "is_staff")
    return JsonResponse(list(users), safe=False)


@csrf_exempt
@login_required(login_url='/accounts/login')
def add_user_ajax(request):
    if not request.user.is_staff:
        return JsonResponse({"error": "Forbidden"}, status=403)

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get("username")
            email = data.get("email")
            password = data.get("password")

            if not username or not password:
                return JsonResponse({"error": "Username dan password wajib diisi"}, status=400)

            # cek apakah username sudah ada
            if UserProfile.objects.filter(username=username).exists():
                return JsonResponse({"error": "Username sudah terpakai"}, status=400)

            new_user = UserProfile.objects.create(
                username=username,
                email=email,
                password=make_password(password)
            )

            return JsonResponse({
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "is_staff": new_user.is_staff
            }, status=201)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    else:
        return JsonResponse({"error": "Invalid method"}, status=405)

def public_profile_view(request, username):
    user_target = get_object_or_404(UserProfile, username=username)

    if request.user == user_target:
        return redirect("userprofile:my-profile")

    context = {
        "target_user": user_target
    }
    return render(request, "public_profile.html", context)

@csrf_exempt
def loginapp(request):
    username = request.POST['username']
    password = request.POST['password']
    
    user = authenticate(username=username, password=password)
    if user is not None:
        login(request, user)
        return JsonResponse({
            "username": user.username,
            "status": True,
            "message": "Login successful!",
            "nama": user.nama,
            "umur": user.umur,
            "nomor_telepon": user.nomor_telepon,
            "category_experience": user.category_experience,
            "jenis_kelamin": user.jenis_kelamin,
        }, status=200)

    else:
        return JsonResponse({
            "status": False,
            "message": "Login gagal, mohon cek kembali username dan password anda."
        }, status=401)


@csrf_exempt
def registerapp(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data['username']
        password1 = data['password1']
        password2 = data['password2']

        nama = data.get('nama', username)
        umur = data.get('umur')
        nomor_telepon = data.get('nomor_telepon', '')
        jenis_kelamin = data.get('jenis_kelamin')
        category_experience = data.get('category_experience', 'beginner')
        email = data.get('email', '').strip()

        # cek password
        if password1 != password2:
            return JsonResponse({
                "status": False,
                "message": "Kedua password tidak cocok."
            }, status=400)
        
        # cek username
        if UserProfile.objects.filter(username=username).exists():
            return JsonResponse({
                "status": False,
                "message": "Username sudah dipakai."
            }, status=400)
        
        # buat user baru
        user = UserProfile.objects.create_user(
            username=username,
            password=password1,
            nama=nama,
            umur=umur,
            nomor_telepon=nomor_telepon,
            jenis_kelamin=jenis_kelamin,
            category_experience=category_experience,
            email=email,
        )
        user.save()
        
        return JsonResponse({
            "username": user.username,
            "status": 'success',
            "message": "Akun sukses dibuat!"
        }, status=200)
    
    else:
        return JsonResponse({
            "status": False,
            "message": "Invalid request method."
        }, status=400)
    

@csrf_exempt
def logoutapp(request):
    username = request.user.username if request.user.is_authenticated else None
    try:
        logout(request)
        return JsonResponse({
            "username": username,
            "status": True,
            "message": "Logout sukses!"
        }, status=200)
    except:
        return JsonResponse({
            "status": False,
            "message": "Logout gagal."
        }, status=401)
    
@csrf_exempt
def profileapp(request):
    # pastikan user sudah login
    if not request.user.is_authenticated:
        return JsonResponse({
            "status": False,
            "message": "Authentication required."
        }, status=401)

    user = request.user

    # GET: return data profil
    if request.method == "GET":
        # ambil riwayat pendakian sebagai list nama gunung
        history = list(user.history_gunung.values_list("name", flat=True))

        return JsonResponse({
            "status": True,
            "username": user.username,
            "nama": user.nama or "",
            "umur": user.umur,
            "nomor_telepon": user.nomor_telepon or "",
            "email": user.email or "",
            "category_experience": user.category_experience,
            "jenis_kelamin": user.jenis_kelamin,
            "is_staff": user.is_staff,
            "history_gunung": history,
        }, status=200)

    # POST: update data profil
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON."
            }, status=400)

        nama = data.get("nama", "").strip()
        umur = data.get("umur")
        nomor_telepon = data.get("nomor_telepon", "").strip()
        email = data.get("email", "").strip()
        category_experience = data.get("category_experience")
        jenis_kelamin = data.get("jenis_kelamin")

        user.umur = umur
        user.nomor_telepon = nomor_telepon
        user.email = email
        if category_experience in dict(UserProfile.EXPERIENCE_CHOICES):
            user.category_experience = category_experience
        if jenis_kelamin in dict(UserProfile.GENDER_CHOICES) or jenis_kelamin in (None, ""):
            user.jenis_kelamin = jenis_kelamin or None

        user.nama = nama
        user.save()

        return JsonResponse({
            "status": True,
            "message": "Profil berhasil diperbarui."
        }, status=200)

    else:
        return JsonResponse({
            "status": False,
            "message": "Invalid request method."
        }, status=405)
    
@csrf_exempt
@login_required(login_url='/accounts/login')
def manage_user_app(request):
    if not request.user.is_staff:
        return JsonResponse({"error": "Forbidden"}, status=403)

    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    user_id = data.get("user_id")
    action = data.get("action")

    if not user_id or action not in ("toggle", "delete"):
        return JsonResponse({"error": "Invalid parameters"}, status=400)

    try:
        target_user = UserProfile.objects.get(id=user_id)
    except UserProfile.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

    if target_user == request.user:
        return JsonResponse({
            "success": False,
            "message": "Tidak bisa mengubah atau menghapus diri sendiri."
        }, status=400)

    if action == "toggle":
        target_user.is_staff = not target_user.is_staff
        target_user.save()
        return JsonResponse({
            "success": True,
            "message": "Status admin diperbarui.",
            "is_staff": target_user.is_staff,
        }, status=200)

    elif action == "delete":
        target_user.delete()
        return JsonResponse({
            "success": True,
            "message": "User berhasil dihapus."
        }, status=200)

