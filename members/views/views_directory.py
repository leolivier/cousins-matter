# util functions for member views
from typing import Any
from django.shortcuts import render
from django.utils.translation import gettext as _
import io
from reportlab.rl_config import defaultPageSize
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from django.http import FileResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.utils.text import slugify
from django.conf import settings

from cousinsmatter.utils import Paginator

from ..models import Member

LIST_STYLE = TableStyle(
    [
        ('LINEABOVE', (0, 0), (-1, 1), 2, colors.green),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
        ('LINEABOVE', (0, 2), (-1, -1), 0.25, colors.black),
        ('LINEBELOW', (0, -1), (-1, -1), 2, colors.green),
        ('ROWBACKGROUNDS', (0, 2), (-1, -1), [colors.lightgrey, colors.white])
    ]
)


class MembersDirectoryView(LoginRequiredMixin, generic.View):
    template_name = "members/members/members_directory.html"
    model = Member

    def get(self, request, page_num=1) -> dict[str, Any]:
      members = Member.objects.alive()
      page = Paginator.get_page(request, members, page_num, "members:directory_page", 100)
      return render(request, self.template_name, {"page": page})


class MembersPrintDirectoryView(LoginRequiredMixin, generic.View):

    def get(self, request):
      buffer = self._generate_directory_pdf()
      # FileResponse sets the Content-Disposition header so that browsers
      # present the option to save the file.
      filename = f"{slugify(self.title())}.pdf"
      return FileResponse(buffer, as_attachment=True, filename=filename)

    def title(self):
        return _('%(site_name)s directory') % {'site_name': settings.SITE_NAME}

    def _get_directory_data(self):
      dir_data = [[_("Name"), _("Phone"), _('Email'), _("Address")]]
      for member in Member.objects.alive():
          dir_data.append([member.full_name,
                          member.phone if member.phone else "",
                          member.email,
                          member.address.__str__() if member.address else ""
                           ])
      return dir_data

    def _generate_directory_pdf(self):

      pdf_size = defaultPageSize
      if settings.PDF_SIZE == 'A4':
          pdf_size = A4
      elif settings.PDF_SIZE == 'letter':
          pdf_size = letter

      title = self.title()

      def add_footer(canvas, doc):
          canvas.saveState()
          canvas.setFont('Times-Roman', 9)
          canvas.drawString(inch, 0.75 * inch, _("Page %(doc_page)s - %(title)s") % {'doc_page': doc.page, 'title': title})
          canvas.restoreState()

      def handle_first_page(canvas, doc):
          PAGE_WIDTH = pdf_size[0]
          PAGE_HEIGHT = pdf_size[1]
          canvas.saveState()
          canvas.setFont('Times-Bold', 16)
          canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT-0.5*inch, title)
          canvas.restoreState()
          add_footer(canvas, doc)

      Story = []
      data = self._get_directory_data()
      dir_table = Table(data, style=LIST_STYLE, repeatRows=1)
      Story.append(dir_table)

      buffer = io.BytesIO()
      doc = SimpleDocTemplate(buffer, pageSize=pdf_size)
      doc.build(Story, onFirstPage=handle_first_page, onLaterPages=add_footer)
      buffer.seek(0)
      return buffer
