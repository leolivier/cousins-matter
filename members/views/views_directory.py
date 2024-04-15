# util functions for member views
from django.utils.translation import gettext as _
from django.shortcuts import redirect
import io
from reportlab.rl_config import defaultPageSize
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle,Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from django.http import FileResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic

from cousinsmatter import settings
from ..models import Member

LIST_STYLE = TableStyle(
    [
        ('LINEABOVE', (0,0), (-1,1), 2, colors.green),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
        ('LINEABOVE', (0,2), (-1,-1), 0.25, colors.black),
        ('LINEBELOW', (0,-1), (-1,-1), 2, colors.green),
        ('ROWBACKGROUNDS', (0,2), (-1,-1), [colors.lightgrey, colors.white])
    ]
)

class MembersDirectoryView(LoginRequiredMixin, generic.ListView):
    template_name = "members/members_directory.html"
    paginate_by = 100
    model = Member
    
class MembersPrintDirectoryView(LoginRequiredMixin, generic.View):
    
    def get(self, request):
      buffer = self._generate_directory_pdf()
      # FileResponse sets the Content-Disposition header so that browsers
      # present the option to save the file.
      return FileResponse(buffer, as_attachment=True, filename="directory.pdf")

    def _get_directory_data(self):
      dir_data = [[_("Name"), _("Phone"), _('Email'), _("Address")]]
      for member in Member.objects.all():
          dir_data.append([member.get_full_name(), 
                      member.phone if member.phone else "", 
                      member.email(), 
                      member.address.__str__() if member.address else ""
                      ])
      return dir_data
       
    def _generate_directory_pdf(self):
      
      match settings.PDF_SIZE:
          case 'A4': pdf_size=A4
          case 'letter': pdf_size=letter
          case _: pdf_size = defaultPageSize
      
      title=_(f'{settings.SITE_NAME} directory')

      def add_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Times-Roman',9)
        canvas.drawString(inch, 0.75 * inch, _("Page %d %s") % (doc.page, title))
        canvas.restoreState()

      def handle_first_page(canvas, doc):
        PAGE_WIDTH = pdf_size[0]
        PAGE_HEIGHT = pdf_size[1]
        canvas.saveState()
        canvas.setFont('Times-Bold',16)
        canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT-0.5*inch, title)
        canvas.restoreState()
        add_footer(canvas, doc)

      Story = [] #[Spacer(1, 0.4*inch)]
      # create a table containing the directory data
      data = self._get_directory_data()
      for i in range(10):
        data += self._get_directory_data()
      dir_table = Table(data, style=LIST_STYLE, repeatRows=1)
      Story.append(dir_table)
      
      # Create a file-like buffer to receive PDF data.
      buffer = io.BytesIO()
      # provide the buffer as "memory file"
      doc = SimpleDocTemplate(buffer, pageSize=pdf_size)
      # build the doc, this fills the buffer
      doc.build(Story, onFirstPage=handle_first_page, onLaterPages=add_footer)
      # reset buffer to beginning
      buffer.seek(0)
      return buffer
