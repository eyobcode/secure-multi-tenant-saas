from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
# from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

User = get_user_model()

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("/")
            else:
                return render(request, "auth/login.html", {
                    "error": "Invalid username or password"
                })
        else:
            return render(request, "auth/login.html", {
                "error": "Missing username or password"
            })

    return render(request, "auth/login.html")

def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if username and password:
            if User.objects.filter(username=username).exists():
                return render(request, "auth/register.html", {
                    "error": "Username already taken"
                })
            try:
                user = User.objects.create_user(username=username, password=password)
                login(request, user)
                return redirect("/")
            except Exception as e:
                return render(request, "auth/register.html", {
                    "error": f"Error creating user: {str(e)}"
                })
        else:
            return render(request, "auth/register.html", {
                "error": "Missing username or password"
            })

    return render(request, "auth/register.html")