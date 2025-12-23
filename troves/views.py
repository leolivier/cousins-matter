from urllib.parse import urlencode
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from cm_main.utils import PageOutOfBounds, Paginator, assert_request_is_ajax
from members.models import Member
from cm_main.utils import check_edit_permission
from .models import Trove
from .forms import TreasureForm


@login_required
def trove_cave(request, page=1):
  category = request.GET.get("category")
  if category and category in dict(Trove.CATEGORY_CHOICES).keys():
    treasures = Trove.objects.filter(category=category).order_by("id")

    def compute_link(idx):
      return reverse("troves:page", args=[idx]) + "?" + urlencode({"category": category})
  else:
    treasures = Trove.objects.all().order_by("category", "id")

    def compute_link(idx):
      return reverse("troves:page", args=[idx])

  try:
    trove_page = Paginator.get_page(
      request,
      object_list=treasures,
      page_num=page,
      compute_link=compute_link,
      default_page_size=settings.DEFAULT_TROVE_PAGE_SIZE,
      group_by="category",
    )
    return render(
      request,
      "troves/trove_cave.html",
      {"page": trove_page, "trove_categories": Trove.CATEGORY_CHOICES},
    )
  except PageOutOfBounds as exc:
    return redirect(exc.redirect_to)


@login_required
def create_treasure(request):
  if request.method == "POST":
    form = TreasureForm(request.POST, request.FILES)
    owner = Member.objects.only("id").get(id=request.user.id)
    form.instance.owner_id = owner.id
    if form.is_valid():
      try:
        form.save()
        return redirect(reverse("troves:list"))  # try to go to last page
      except Exception as e:
        messages.error(request, str(e))
        return render(request, "troves/treasure_form.html", {"form": form})
  else:
    form = TreasureForm()
  return render(request, "troves/treasure_form.html", {"form": form})


@login_required
def update_treasure(request, pk):
  treasure = get_object_or_404(Trove, pk=pk)
  check_edit_permission(request, treasure.owner)
  if request.method == "POST":
    form = TreasureForm(request.POST, request.FILES, instance=treasure)
    if form.is_valid():
      form.save()
      return redirect(reverse("troves:list"))  # try to go to last page
  else:
    form = TreasureForm(instance=treasure)
  return render(request, "troves/treasure_form.html", {"form": form})


@csrf_exempt
@login_required
def delete_treasure(request, pk):
  assert_request_is_ajax(request)
  try:
    treasure = get_object_or_404(Trove, pk=pk)
    check_edit_permission(request, treasure.owner())
    treasure.delete()
    return JsonResponse({"deleted": True})
  except Exception:
    return JsonResponse({"deleted": False})


@login_required
def treasure_detail(request, pk):
  try:
    treasure = get_object_or_404(Trove, pk=pk)
    return render(request, "troves/treasure_detail.html", {"treasure": treasure})
  except Exception as e:
    messages.error(request, f"Exception: {e}")
    return redirect(reverse(("troves:list")))
