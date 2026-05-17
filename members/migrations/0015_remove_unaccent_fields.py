# Generated manually to remove unaccent fields for PostgreSQL native support

from django.db import migrations, models
from django.contrib.postgres.operations import TrigramExtension


class Migration(migrations.Migration):
    dependencies = [
        ("members", "0014_alter_member_email_batch_frequency"),
    ]

    operations = [
        # Remove old unaccent indexes
        migrations.RemoveIndex(
            model_name="member",
            name="members_mem_first_n_feb60f_idx",
        ),
        migrations.RemoveIndex(
            model_name="member",
            name="members_mem_last_na_79ca5b_idx",
        ),
        # Remove unaccent fields
        migrations.RemoveField(
            model_name="member",
            name="first_name_unaccent",
        ),
        migrations.RemoveField(
            model_name="member",
            name="last_name_unaccent",
        ),
        # Add new indexes on first_name and last_name
        migrations.AddIndex(
            model_name="member",
            index=models.Index(fields=["first_name"], name="members_mem_first_n_13b9bb_idx"),
        ),
        migrations.AddIndex(
            model_name="member",
            index=models.Index(fields=["last_name"], name="members_mem_last_na_e41db7_idx"),
        ),
        TrigramExtension(),
    ]
