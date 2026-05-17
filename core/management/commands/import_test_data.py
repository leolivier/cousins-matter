import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.apps import apps


class Command(BaseCommand):
  help = "Imports test data from <app>/tests/resources/fixtures.json for each app."

  def add_arguments(self, parser):
    parser.add_argument("--app", type=str, help="Import data for a specific app")

  def handle(self, *args, **options):
    target_app = options.get("app")

    if target_app:
      app_list = [target_app]
    else:
      # Order might matter due to FKs
      app_list = ["members", "pages", "polls", "chat", "forum", "galleries", "classified_ads", "genealogy", "troves", "core"]

    for app_label in app_list:
      try:
        app_config = apps.get_app_config(app_label)
        fixture_path = os.path.join(app_config.path, "tests", "resources", "fixtures.json")

        if os.path.exists(fixture_path):
          self.stdout.write(f"Importing fixtures for {app_label} from {fixture_path}...")
          # We use the absolute path to make sure loaddata finds it
          call_command("loaddata", fixture_path)
          self.stdout.write(self.style.SUCCESS(f"  Successfully imported {app_label}"))
        else:
          if target_app:
            self.stdout.write(self.style.WARNING(f"Fixture not found at {fixture_path}"))
          else:
            self.stdout.write(f"No fixture found for {app_label}, skipping.")

      except Exception as e:
        self.stdout.write(self.style.ERROR(f"Failed to import data for {app_label}: {e}"))

    self.stdout.write(self.style.SUCCESS("Import completed!"))
