from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404
from django_sendfile import sendfile

from sport.models import Reference, SelfSportReport, MedicalGroupReference


def download_student_object(
        request,
        klass,
        student_id: int,
        **kwargs
):
    user = request.user
    if user.is_staff or user.pk == student_id:
        requested_entry = get_object_or_404(
            klass,
            student_id=student_id,
            **kwargs,
        )
        return sendfile(request, requested_entry.image.path)
    else:
        raise Http404()


@login_required
def medical_reference_download(
        request,
        semester_name: str,
        student_id: int,
        filename: str,
):
    requested_path = request.path[len(settings.MEDIA_URL):]
    return download_student_object(
        request,
        Reference,
        student_id,
        semester__name=semester_name,
        image=requested_path,
    )


@login_required
def self_sport_download(
        request,
        semester_name: str,
        student_id: int,
        filename: str,
):
    requested_path = request.path[len(settings.MEDIA_URL):]
    return download_student_object(
        request,
        SelfSportReport,
        student_id,
        semester__name=semester_name,
        image=requested_path
    )


@login_required
def medical_group_reference_download(
        request,
        student_id: int,
        filename: str,
):
    requested_path = request.path[len(settings.MEDIA_URL):]
    return download_student_object(
        request,
        MedicalGroupReference,
        student_id,
        image=requested_path
    )
