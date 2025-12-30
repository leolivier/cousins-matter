from django.urls import path
from django.views.decorators.cache import cache_page
from .views import views_family_chart, views_family, views_person, views_dashboard_stats, views_gedcom

app_name = "genealogy"

urlpatterns = [
  path("", views_dashboard_stats.dashboard, name="dashboard"),
  path("people/", views_person.person_list, name="person_list"),
  path("people/page/<int:page_num>/", views_person.person_list, name="person_list_page"),
  path("people/add/", views_person.person_create, name="person_create"),
  path("people/<int:pk>/", views_person.person_detail, name="person_detail"),
  path("people/<int:pk>/edit/", views_person.person_update, name="person_update"),
  path("people/<int:pk>/delete/", views_person.person_delete, name="person_delete"),
  path("families/", views_family.family_list, name="family_list"),
  path("families/page/<int:page_num>/", views_family.family_list, name="family_list_page"),
  path("families/add/", views_family.family_create, name="family_create"),
  path("families/<int:pk>/edit/", views_family.family_update, name="family_update"),
  path("families/<int:pk>/delete/", views_family.family_delete, name="family_delete"),
  path("import/", views_gedcom.import_gedcom, name="import_gedcom"),
  path("export/", views_gedcom.export_gedcom, name="export_gedcom"),
  path("download-gedcom/", views_gedcom.download_gedcom, name="download_gedcom"),
  path("download.ged", views_gedcom.download_gedcom, name="download_gedcom_file"),
  path("family-chart/", views_family_chart.family_chart_view, name="family_chart"),
  path(
    "family-chart/<int:main_person_id>/",
    views_family_chart.family_chart_view,
    name="person_chart",
  ),
  path("api/family-chart-data/", views_family_chart.family_chart_data, name="family_chart_data"),
  path("statistics/", views_dashboard_stats.statistics, name="statistics"),
  path("refresh/", views_dashboard_stats.refresh, name="refresh"),
]
