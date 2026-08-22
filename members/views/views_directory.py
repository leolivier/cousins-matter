# util functions for member views
from io import BytesIO

from django.http import FileResponse, HttpResponse
from django.shortcuts import redirect, render
from django.utils.text import slugify
from django.views import generic

from core.utils import PageOutOfBounds, Paginator

from ..models import Member
from ..services.directory import generate_directory_pdf


class MembersDirectoryView(generic.View):
  template_name = "members/members/members_directory.html"
  model = Member

  def get(self, request, page_num=1) -> HttpResponse:
    members = Member.objects.alive().select_related("address")
    try:
      page = Paginator.get_page(
        request,
        object_list=members,
        page_num=page_num,
        reverse_link="members:directory_page",
        default_page_size=100,
      )
      return render(request, self.template_name, {"page": page})
    except PageOutOfBounds as exc:
      return redirect(exc.redirect_to)


class MembersPrintDirectoryView(generic.View):
  def get(self, request):
    pdf = generate_directory_pdf()

    pdf_content = pdf.output(dest="S")
    if isinstance(pdf_content, str):
      pdf_content = pdf_content.encode("latin1")
    buffer = BytesIO(pdf_content)
    buffer.seek(0)
    filename = f"{slugify(pdf.title)}.pdf"

    # pdf.output(dest='F', name=filename)
    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.
    response = FileResponse(buffer, as_attachment=True, filename=filename)
    response["Content-Type"] = "application/pdf"
    return response
