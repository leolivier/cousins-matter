import logging
import re
from fpdf import FPDF
from typing import Generator

from django.conf import settings
from django.contrib.staticfiles import finders
from django.utils.translation import gettext as _

from ..models import Member

logger = logging.getLogger(__name__)


def get_static_path(filename):
  return finders.find(filename) or None


class DirectoryPDF(FPDF):
  # table headers
  col_widths = [50, 30, 60, 60]  # width of each column
  col_height = 10
  alignments = ["L", "R", "L", "L"]

  def __init__(self, orientation, unit, format):
    super().__init__(orientation, unit, format)
    self.set_title(_("%(site_name)s directory") % {"site_name": settings.SITE_NAME})
    self.alias_nb_pages()
    self.add_page()
    usable_width = self.w - self.l_margin - self.r_margin
    k = usable_width / sum(self.col_widths)
    self.col_widths = [width * k for width in self.col_widths]

  def header(self):
    # Logo
    logo = (
      settings.SITE_LOGO if settings.SITE_LOGO.startswith(settings.PUBLIC_MEDIA_URL) else get_static_path(settings.SITE_LOGO)
    )
    self.image(logo, 10, 8, 33)
    # Arial bold 15
    self.set_font("Arial", "B", 8)
    # Move to the right
    self.cell(60)
    # Title
    self.cell(60, 10, self.title or "", 1, 0, "C")
    # Line break
    self.ln(20)

  # Page footer
  def footer(self):
    # Position at 1.5 cm from bottom
    self.set_y(-15)
    # Arial italic 8
    self.set_font("Arial", "I", 8)
    # Page number + title
    footer_s = _("Page %(doc_page)s - %(title)s") % {
      "doc_page": str(self.page_no()) + "/" + "{nb}",
      "title": self.title,
    }
    self.cell(0, 10, footer_s, 0, 0, "C")

  def draw_table_header(self):
    self.set_fill_color(200, 220, 255)  # background color for header
    for i, header in enumerate([_("Name"), _("Phone"), _("Email"), _("Address")]):
      x_cell = self.get_x()
      y_cell = self.get_y()
      self.multi_cell(
        self.col_widths[i],
        self.col_height,
        header,
        border=1,
        align="C",
        fill=True,
      )
      # Move back to the same height for the next cell
      self.set_xy(x_cell + self.col_widths[i], y_cell)
    self.ln(self.col_height)  # line break for content

  def draw_table_row(self, member):
    # For each line, the line break must be managed according to the content.
    # We can calculate the height required for the longest cell
    cell_heights = []
    for i, datum in enumerate(member):
      # Cut text if too long according to column width
      # Using multi_cell with split_only to obtain the effective height (it doesn't display anything)
      lines = self.multi_cell(
        self.col_widths[i],
        self.col_height,
        datum,
        border=0,
        align=self.alignments[i],
        split_only=True,
      )
      cell_heights.append(len(lines))
    max_lines = max(cell_heights)
    final_height = self.col_height * max_lines

    # if not enough space, for the next line, add a page and redraw header
    if self.get_y() + final_height > self.page_break_trigger:
      self.add_page()
      self.draw_table_header()
    # For each cell in the line, a multi_cell is drawn in a dedicated area.
    for i, datum in enumerate(member):
      x_cell = self.get_x()
      y_cell = self.get_y()

      if cell_heights[i] < max_lines:  # add newlines for having the right box height
        datum += "\n" * (max_lines - cell_heights[i] + 1)
      # The cell is drawn at the calculated position
      lines = self.multi_cell(
        self.col_widths[i],
        self.col_height,
        datum,
        border=1,
        align=self.alignments[i],
      )
      # Move back to the same height for the next cell
      self.set_xy(x_cell + self.col_widths[i], y_cell)
    # Go to the next line once the line is finished
    self.ln(final_height)


def _get_directory_data() -> Generator[list, None, None]:
  for member in Member.objects.alive().select_related("address"):
    yield [
      member.full_name,
      member.phone if member.phone else "",
      member.email,
      re.sub(r"\n\n+", "\n", member.address.__str__().strip(" \n")) if member.address else "",
    ]


def generate_directory_pdf() -> DirectoryPDF:
  pdf = DirectoryPDF("P", "mm", settings.PDF_SIZE)
  pdf.draw_table_header()
  for member in _get_directory_data():
    pdf.draw_table_row(member)
  return pdf
