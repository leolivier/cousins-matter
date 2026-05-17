import os
from django.core.management.base import BaseCommand
from django.core import serializers
from django.apps import apps


class Command(BaseCommand):
  help = "Generates test data using factories and saves them as fixtures in each app's resources folder."

  def add_arguments(self, parser):
    parser.add_argument("--app", type=str, help="Generate data for a specific app")
    parser.add_argument("--count", type=int, default=5, help="Number of instances to generate per model")

  def handle(self, *args, **options):
    target_app = options.get("app")
    count = options.get("count")

    app_list = (
      [target_app]
      if target_app
      else ["members", "polls", "chat", "forum", "galleries", "classified_ads", "genealogy", "troves", "pages", "core"]
    )

    for app_label in app_list:
      self.stdout.write(f"Generating data for app: {app_label}...")

      try:
        # Import the factories for the app
        factories_module = f"{app_label}.tests.factories"
        try:
          import importlib

          module = importlib.import_module(factories_module)
        except ImportError as e:
          self.stdout.write(self.style.WARNING(f"No factories found for {app_label}: {e}"))
          continue

        # Find all factories in the module
        from factory.django import DjangoModelFactory

        factories = [
          obj
          for name, obj in module.__dict__.items()
          if isinstance(obj, type) and issubclass(obj, DjangoModelFactory) and obj != DjangoModelFactory
        ]

        # Generate instances
        generated_objects = []
        for factory_class in factories:
          self.stdout.write(f"  Generating {count} instances for {factory_class._meta.model.__name__}...")
          for _ in range(count):
            try:
              # Use create() to save to DB so we can serialize with PKs
              obj = factory_class.create()
              generated_objects.append(obj)
            except Exception as e:
              import traceback

              self.stdout.write(self.style.ERROR(f"    Error generating {factory_class._meta.model.__name__}: {e}"))
              traceback.print_exc()

        # Dump to JSON
        if generated_objects:
          app_config = apps.get_app_config(app_label)
          resources_dir = os.path.join(app_config.path, "tests", "resources")
          os.makedirs(resources_dir, exist_ok=True)
          fixture_path = os.path.join(resources_dir, "fixtures.json")

          self.stdout.write(f"  Saving fixtures to {fixture_path}...")
          data = serializers.serialize("json", generated_objects, indent=2)
          with open(fixture_path, "w", encoding="utf-8") as f:
            f.write(data)

        self.stdout.write(self.style.SUCCESS(f"Finished {app_label}"))

      except Exception as e:
        self.stdout.write(self.style.ERROR(f"Failed to generate data for {app_label}: {e}"))

    self.stdout.write(self.style.SUCCESS("All done!"))
