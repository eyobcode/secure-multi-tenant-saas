from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required()
def profile_list_view(request):
    user = request.user

    context = {
        "object_list": User.objects.filter(is_active=True),
    }

    user_groups = user.groups.all()

    if user_groups.filter(name__icontains="basic").exists():
        return HttpResponse("congrats")

    print("is_staff:", user.is_staff)
    print("user ===> :", user)

    return render(request, "profiles/list.html", context)


@login_required()
def profile_view(request,username=None, *args, **kwargs):
    user = request.user
    profile_user_obj = get_object_or_404(User, username=username)

    print(user.has_perm('auth.view_user'))
    # profile_user_obj = User.objects.get(username=username)
    is_me = user == profile_user_obj
    # print("user ==> :",user, profile_user_obj, "is_me:", user == profile_user_obj)
    return HttpResponse(f"Hello there {username} - {profile_user_obj.id} - {user.id}, -- {is_me}")
