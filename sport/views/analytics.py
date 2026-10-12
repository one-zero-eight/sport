from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render


@login_required
@permission_required('IsTrainer')
def analytics_view(request, **kwargs):
    return render(
        request,
        "analytics.html",
        context={"current_user": request.user,
                 "current_user_full_name": request.user.first_name+" "+request.user.last_name}
    )
