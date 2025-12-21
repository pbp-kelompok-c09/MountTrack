from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .forms import CommentForm, EventForm
from .models import CommunityEvent, EventJoin, Comment


def event_list(request):
    qs = CommunityEvent.objects.exclude(status=CommunityEvent.Status.CANCELLED).order_by("start_at")

    # Ambil parameter dari form
    search_q = request.GET.get("search")
    status_q = request.GET.get("status")
    difficulty_q = request.GET.get("difficulty")

    # 🔍 Filter berdasarkan gunung / nama event
    if search_q:
        qs = qs.filter(
            mountain_name__icontains=search_q
        ) | qs.filter(title__icontains=search_q)

    # Filter status (opsional)
    if status_q:
        qs = qs.filter(status=status_q)

    
    if difficulty_q:
        qs = qs.filter(difficulty__iexact=difficulty_q)

    # Pagination
    paginator = Paginator(qs, 12)
    page = request.GET.get("page")
    events = paginator.get_page(page)

    # Return JSON
    events_data = []
    for event in events:
        events_data.append({
            "id": event.pk,
            "title": event.title,
            "mountain_name": event.mountain_name,
            "start_at": event.start_at.isoformat() if event.start_at else None,
            "end_at": event.end_at.isoformat() if event.end_at else None,
            "capacity": event.capacity,
            "price": str(event.price) if event.price else None,
            "difficulty": event.difficulty,
            "meeting_point": event.meeting_point,
            "contact_person": event.contact_person,
            "organizer": {
                "id": event.organizer.id,
                "username": event.organizer.username,
                "nama": event.organizer.nama,
            },
            "description": event.description,
            "status": event.status,
            "created_at": event.created_at.isoformat(),
            "confirmed_count": event.confirmed_count(),
            "waitlist_count": event.waitlist_count(),
            "is_full": event.is_full(),
        })

    return JsonResponse({
        "success": True,
        "events": events_data,
        "has_next": events.has_next(),
        "has_previous": events.has_previous(),
        "current_page": events.number,
        "total_pages": paginator.num_pages,
        "total_count": paginator.count,
    })



def event_detail(request, pk):
    event = get_object_or_404(CommunityEvent, pk=pk)
    
    if request.method == "POST" and request.user.is_authenticated:
        try:
            data = json.loads(request.body)
            body = data.get('body', '')
            if not body:
                return JsonResponse({"success": False, "message": "Komentar tidak boleh kosong"}, status=400)
            
            comment = Comment.objects.create(
                event=event,
                user=request.user,
                body=body
            )
            return JsonResponse({
                "success": True,
                "message": "Komentar terkirim.",
                "comment": {
                    "id": comment.id,
                    "body": comment.body,
                    "user": {
                        "id": request.user.id,
                        "username": request.user.username,
                        "nama": request.user.nama,
                    },
                    "created_at": comment.created_at.isoformat(),
                }
            })
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=400)

    user_join = None
    user_join_status = None
    if request.user.is_authenticated:
        user_join = EventJoin.objects.filter(event=event, user=request.user).first()
        if user_join:
            user_join_status = user_join.status

    comments_data = []
    for comment in event.comments.all():
        comments_data.append({
            "id": comment.id,
            "body": comment.body,
            "user": {
                "id": comment.user.id,
                "username": comment.user.username,
                "nama": comment.user.nama,
            },
            "created_at": comment.created_at.isoformat(),
        })

    return JsonResponse({
        "success": True,
        "event": {
            "id": event.pk,
            "title": event.title,
            "mountain_name": event.mountain_name,
            "start_at": event.start_at.isoformat() if event.start_at else None,
            "end_at": event.end_at.isoformat() if event.end_at else None,
            "capacity": event.capacity,
            "price": str(event.price) if event.price else None,
            "difficulty": event.difficulty,
            "meeting_point": event.meeting_point,
            "contact_person": event.contact_person,
            "organizer": {
                "id": event.organizer.id,
                "username": event.organizer.username,
                "nama": event.organizer.nama,
            },
            "description": event.description,
            "status": event.status,
            "created_at": event.created_at.isoformat(),
            "confirmed_count": event.confirmed_count(),
            "waitlist_count": event.waitlist_count(),
            "is_full": event.is_full(),
        },
        "comments": comments_data,
        "user_join_status": user_join_status,
    })


@login_required
def event_create(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            form = EventForm(data)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.organizer = request.user
                obj.save()
                return JsonResponse({
                    "success": True,
                    "message": "Event berhasil dibuat.",
                    "event_id": obj.pk,
                    "event": {
                        "id": obj.pk,
                        "title": obj.title,
                        "mountain_name": obj.mountain_name,
                        "start_at": obj.start_at.isoformat() if obj.start_at else None,
                        "end_at": obj.end_at.isoformat() if obj.end_at else None,
                        "capacity": obj.capacity,
                        "price": str(obj.price) if obj.price else None,
                        "difficulty": obj.difficulty,
                        "meeting_point": obj.meeting_point,
                        "contact_person": obj.contact_person,
                        "description": obj.description,
                        "status": obj.status,
                    }
                })
            else:
                return JsonResponse({"success": False, "errors": form.errors}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=400)
    else:
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)


@login_required
def event_edit(request, pk):
    event = get_object_or_404(CommunityEvent, pk=pk, organizer=request.user)
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            form = EventForm(data, instance=event)
            if form.is_valid():
                obj = form.save()
                return JsonResponse({
                    "success": True,
                    "message": "Event diperbarui.",
                    "event": {
                        "id": obj.pk,
                        "title": obj.title,
                        "mountain_name": obj.mountain_name,
                        "start_at": obj.start_at.isoformat() if obj.start_at else None,
                        "end_at": obj.end_at.isoformat() if obj.end_at else None,
                        "capacity": obj.capacity,
                        "price": str(obj.price) if obj.price else None,
                        "difficulty": obj.difficulty,
                        "meeting_point": obj.meeting_point,
                        "contact_person": obj.contact_person,
                        "description": obj.description,
                        "status": obj.status,
                    }
                })
            else:
                return JsonResponse({"success": False, "errors": form.errors}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=400)
    else:
        return JsonResponse({
            "success": True,
            "event": {
                "id": event.pk,
                "title": event.title,
                "mountain_name": event.mountain_name,
                "start_at": event.start_at.isoformat() if event.start_at else None,
                "end_at": event.end_at.isoformat() if event.end_at else None,
                "capacity": event.capacity,
                "price": str(event.price) if event.price else None,
                "difficulty": event.difficulty,
                "meeting_point": event.meeting_point,
                "contact_person": event.contact_person,
                "description": event.description,
                "status": event.status,
            }
        })


@login_required
def event_cancel(request, pk):
    event = get_object_or_404(CommunityEvent, pk=pk, organizer=request.user)
    event.status = CommunityEvent.Status.CANCELLED
    event.save(update_fields=["status"])
    return JsonResponse({
        "success": True,
        "message": "Event dibatalkan.",
        "event_id": event.pk,
        "status": event.status,
    })


@login_required
@transaction.atomic
def event_join(request, pk):
    event = get_object_or_404(CommunityEvent, pk=pk)
    if event.status in [CommunityEvent.Status.CANCELLED, CommunityEvent.Status.DRAFT]:
        return JsonResponse({
            "success": False,
            "message": "Event belum dibuka atau sudah dibatalkan."
        }, status=400)
    
    if event.organizer_id == request.user.id:
        return JsonResponse({
            "success": False,
            "message": "Kamu adalah organizer event ini."
        }, status=400)

    join, created = EventJoin.objects.get_or_create(event=event, user=request.user)
    if not created and join.status == EventJoin.Status.CONFIRMED:
        return JsonResponse({
            "success": False,
            "message": "Kamu sudah terdaftar sebagai peserta."
        }, status=400)

    if event.is_full():
        join.status = EventJoin.Status.WAITLIST
        join.save()
        return JsonResponse({
            "success": True,
            "message": "Kapasitas penuh. Kamu masuk daftar tunggu (waitlist).",
            "join_status": join.status,
            "event_status": event.status,
        })
    else:
        join.status = EventJoin.Status.CONFIRMED
        join.save()
        if event.confirmed_count() >= event.capacity:
            event.status = CommunityEvent.Status.FULL
            event.save(update_fields=["status"])
        return JsonResponse({
            "success": True,
            "message": "Berhasil bergabung.",
            "join_status": join.status,
            "event_status": event.status,
        })


@login_required
@transaction.atomic
def event_leave(request, pk):
    event = get_object_or_404(CommunityEvent, pk=pk)
    join = EventJoin.objects.filter(event=event, user=request.user).first()
    if not join:
        return JsonResponse({
            "success": False,
            "message": "Kamu belum bergabung."
        }, status=400)

    join.status = EventJoin.Status.CANCELLED
    join.save(update_fields=["status"])

    promoted_user = None
    if event.status == CommunityEvent.Status.FULL:
        next_wait = EventJoin.objects.filter(
            event=event, status=EventJoin.Status.WAITLIST
        ).order_by("joined_at").first()
        if next_wait:
            next_wait.status = EventJoin.Status.CONFIRMED
            next_wait.save(update_fields=["status"])
            promoted_user = next_wait.user.username
        if event.confirmed_count() < event.capacity:
            event.status = CommunityEvent.Status.OPEN
            event.save(update_fields=["status"])

    return JsonResponse({
        "success": True,
        "message": "Kamu sudah keluar dari event.",
        "event_status": event.status,
        "promoted_user": promoted_user,
    })
