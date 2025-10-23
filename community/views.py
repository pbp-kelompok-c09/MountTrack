from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.core.paginator import Paginator

from .forms import CommentForm, EventForm
from .models import CommunityEvent, EventJoin

def event_list(request):
    qs = CommunityEvent.objects.exclude(status=CommunityEvent.Status.CANCELLED).order_by("start_at")
    mountain = request.GET.get("mountain")
    status_q = request.GET.get("status")
    if mountain:
        qs = qs.filter(mountain_name__icontains=mountain)
    if status_q:
        qs = qs.filter(status=status_q)
    paginator = Paginator(qs, 12)
    page = request.GET.get("page")
    events = paginator.get_page(page)
    return render(request, "community/event_list.html", {"events": events, "mountain": mountain or "", "status_q": status_q or ""})

def event_detail(request, pk):
    event = get_object_or_404(CommunityEvent, pk=pk)
    comment_form = CommentForm()
    if request.method == "POST" and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            c = comment_form.save(commit=False)
            c.event = event
            c.user = request.user
            c.save()
            messages.success(request, "Komentar terkirim.")
            return redirect("community:event_detail", pk=pk)
    user_join = None
    if request.user.is_authenticated:
        user_join = EventJoin.objects.filter(event=event, user=request.user).first()
    context = {
        "event": event,
        "comment_form": comment_form,
        "comments": event.comments.all(),
        "confirmed_count": event.confirmed_count(),
        "user_join": user_join,
        "now": timezone.now(),
    }
    return render(request, "community/event_detail.html", context)

@login_required
def event_create(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.organizer = request.user
            obj.save()
            messages.success(request, "Event berhasil dibuat.")
            return redirect("community:event_detail", pk=obj.pk)
    else:
        form = EventForm(initial={"status": CommunityEvent.Status.OPEN})
    return render(request, "community/event_form.html", {"form": form, "mode": "create"})

@login_required
def event_edit(request, pk):
    event = get_object_or_404(CommunityEvent, pk=pk, organizer=request.user)
    if request.method == "POST":
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, "Event diperbarui.")
            return redirect("community:event_detail", pk=pk)
    else:
        form = EventForm(instance=event)
    return render(request, "community/event_form.html", {"form": form, "mode": "edit", "event": event})

@login_required
def event_cancel(request, pk):
    event = get_object_or_404(CommunityEvent, pk=pk, organizer=request.user)
    event.status = CommunityEvent.Status.CANCELLED
    event.save(update_fields=["status"])
    messages.warning(request, "Event dibatalkan.")
    return redirect("community:event_detail", pk=pk)

@login_required
@transaction.atomic
def event_join(request, pk):
    event = get_object_or_404(CommunityEvent, pk=pk)
    if event.status in [CommunityEvent.Status.CANCELLED, CommunityEvent.Status.DRAFT]:
        messages.error(request, "Event belum dibuka atau sudah dibatalkan.")
        return redirect("community:event_detail", pk=pk)
    if event.organizer_id == request.user.id:
        messages.info(request, "Kamu adalah organizer event ini.")
        return redirect("community:event_detail", pk=pk)
    join, created = EventJoin.objects.get_or_create(event=event, user=request.user)
    if not created and join.status == EventJoin.Status.CONFIRMED:
        messages.info(request, "Kamu sudah terdaftar sebagai peserta.")
        return redirect("community:event_detail", pk=pk)
    if event.is_full():
        join.status = EventJoin.Status.WAITLIST
        join.save()
        messages.warning(request, "Kapasitas penuh. Kamu masuk daftar tunggu (waitlist).")
    else:
        join.status = EventJoin.Status.CONFIRMED
        join.save()
        if event.confirmed_count() >= event.capacity:
            event.status = CommunityEvent.Status.FULL
            event.save(update_fields=["status"])
        messages.success(request, "Berhasil bergabung.")
    return redirect("community:event_detail", pk=pk)

@login_required
@transaction.atomic
def event_leave(request, pk):
    event = get_object_or_404(CommunityEvent, pk=pk)
    join = EventJoin.objects.filter(event=event, user=request.user).first()
    if not join:
        messages.info(request, "Kamu belum bergabung.")
        return redirect("community:event_detail", pk=pk)
    join.status = EventJoin.Status.CANCELLED
    join.save(update_fields=["status"])
    if event.status == CommunityEvent.Status.FULL:
        next_wait = EventJoin.objects.filter(event=event, status=EventJoin.Status.WAITLIST).order_by("joined_at").first()
        if next_wait:
            next_wait.status = EventJoin.Status.CONFIRMED
            next_wait.save(update_fields=["status"])
        if event.confirmed_count() < event.capacity:
            event.status = CommunityEvent.Status.OPEN
            event.save(update_fields=["status"])
    messages.success(request, "Kamu sudah keluar dari event.")
    return redirect("community:event_detail", pk=pk)
