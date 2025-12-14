from django.urls import path
from . import views

app_name = "genealogy"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("people/", views.person_list, name="person_list"),
    path("people/page/<int:page_num>/", views.person_list, name="person_list_page"),
    path("people/add/", views.person_create, name="person_create"),
    path("people/<int:pk>/", views.person_detail, name="person_detail"),
    path("people/<int:pk>/edit/", views.person_update, name="person_update"),
    path("people/<int:pk>/delete/", views.person_delete, name="person_delete"),
    path("families/", views.family_list, name="family_list"),
    path("families/page/<int:page_num>/", views.family_list, name="family_list_page"),
    path("families/add/", views.family_create, name="family_create"),
    path("families/<int:pk>/edit/", views.family_update, name="family_update"),
    path("families/<int:pk>/delete/", views.family_delete, name="family_delete"),
    path("import/", views.import_gedcom, name="import_gedcom"),
    path("export/", views.export_gedcom, name="export_gedcom"),
    path("download-gedcom/", views.download_gedcom, name="download_gedcom"),
    path("download.ged", views.download_gedcom, name="download_gedcom_file"),
    path("family-chart/", views.family_chart_view, name="family_chart"),
    path(
        "family-chart/<int:main_person_id>/",
        views.family_chart_view,
        name="family_chart",
    ),
    path("api/family-chart-data/", views.family_chart_data, name="family_chart_data"),
    path("statistics/", views.statistics, name="statistics"),
    path("tree/", views.family_tree, name="family_tree"),
    path("api/tree-data/", views.tree_data, name="tree_data"),
    path("refresh/", views.refresh, name="refresh"),
]
