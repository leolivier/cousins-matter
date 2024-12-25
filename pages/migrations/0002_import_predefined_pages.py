from django.core import serializers
from django.db import migrations

parent_pages = []
child_pages = []


def create_child_pages(apps, child_pages):
  BaseFlatPage = apps.get_model("flatpages", "FlatPage")
  CustomFlatPage = apps.get_model("pages", "FlatPage")

  for page in child_pages:
    parent, child = page['parent'], page['child']
    db_parent = BaseFlatPage.objects.filter(url__iexact=parent.url)
    if db_parent.exists():
      db_parent = db_parent.first()
      pk = db_parent.pk
      db_child = CustomFlatPage.objects.filter(pk=pk)
      if db_child.exists():  # child already exists, check if it was updated
        db_child = db_child.first()
        if db_child.updated:  # updated since last import, we can't safely update it
          continue
        if db_child.title != child.title or db_child.content != child.content or db_child.url != child.url:
          db_child.title = child.title
          db_child.content = child.content
          db_child.url = child.url
          db_child.predefined = True
          db_child.save()
      else:  # child doesn't exist, create it as predefined
        db_child = CustomFlatPage(pk=pk, predefined=child.predefined, updated=child.updated)
        db_child.save()
    else:  # parent (and thus child) doesn't exist, create it through its child
      db_child = CustomFlatPage(title=parent.title,
                                content=parent.content,
                                url=parent.url,
                                enable_comments=parent.enable_comments,
                                template_name=parent.template_name,
                                registration_required=parent.registration_required,
                                predefined=child.predefined,
                                updated=child.updated)
      db_child.save()


def load_fixture(apps, schema_editor):

  # Open and load the fixture
  with open('pages/fixtures/predefined_flatpages.json') as fixture_file:
    deserialized = serializers.deserialize('json', fixture_file)
    # print("deserialized", deserialized)
    for item in deserialized:
      obj = item.object
      if obj._meta.app_label == 'flatpages' and obj._meta.model_name == 'flatpage':
        # this is a parent page, just store it
        parent_pages.append(obj)
      elif obj._meta.app_label == 'pages' and obj._meta.model_name == 'flatpage':
        # this is a child page, link it to the parent
        parents = [page for page in parent_pages if page.pk == obj.pk]
        if parents:
          child_pages.append({'child': obj, 'parent': parents[0]})
        else:
          raise ValueError(f"Parent page not found for page {obj.pk}")
      else:
        raise ValueError(f"Unknown object type {type(obj)}")

  create_child_pages(apps, child_pages)


def reverse_fixture(apps, schema_editor):
  # Code to cancel loading if necessary
  CustomFlatPage = apps.get_model("pages", "FlatPage")
  # cancel all predefined non updated pages, they will be recreated on next migration
  CustomFlatPage.objects.filter(predefined=True, updated=False).delete()


class Migration(migrations.Migration):

  dependencies = [
    ('pages', '0001_initial'),
  ]

  operations = [
    migrations.RunPython(load_fixture, reverse_code=reverse_fixture),
  ]
