from django.conf import settings
from django.core import serializers
from django.db import migrations, transaction
import logging

logger = logging.getLogger(__name__)
current_site = None


def createCustomFlatPage(apps, baseFlatPage, predefined, updated, pk=None):
    """
    Creates and saves a custom FlatPage instance using the provided base FlatPage data.

    Args:
        customFlatPageClass: The model class for creating a custom FlatPage.
        baseFlatPage: An instance of the base FlatPage to be used for data extraction.
        predefined (bool): Indicates if the custom FlatPage is predefined.
        updated (bool): Indicates if the custom FlatPage has been updated.
        pk (optional): The primary key of the base flat page to be assigned to the custom
        FlatPage. If None, a new custom FlatPage will be created along with its base FlatPage
        and the site is set post-save.
    """
    CustomFlatPage = apps.get_model("pages", "FlatPage")
    fields = {
        "title": baseFlatPage.title,
        "content": baseFlatPage.content,
        "url": baseFlatPage.url,
        "enable_comments": baseFlatPage.enable_comments,
        "template_name": baseFlatPage.template_name,
        "registration_required": baseFlatPage.registration_required,
        "predefined": predefined,
        "updated": updated,
    }
    if pk:
        fields["pk"] = pk
        logger.info(f"creating custom and updating its base with fields={fields}")
    else:
        logger.info(f"creating custom and base with fields={fields}")
    customFlatPage = CustomFlatPage(**fields)
    customFlatPage.save()


def createSitesRelationship(apps):
    CustomFlatPage = apps.get_model("pages", "FlatPage")
    Site = apps.get_model("sites", "Site")
    global current_site
    site_qs = Site.objects.filter(pk=settings.SITE_ID)
    # site creation is only for tests normally
    current_site = (
        current_site or site_qs.first()
        if site_qs.exists()
        else Site.objects.create(
            pk=settings.SITE_ID,
            domain=settings.SITE_DOMAIN or "example.com",
            name=settings.SITE_NAME,
        )
    )
    # Use bulk_create for the M2M intermediate table
    ThroughModel = CustomFlatPage.sites.through
    sites_relations = []
    for page in CustomFlatPage.objects.filter(sites__isnull=True).distinct():
        sites_relations.append(
            ThroughModel(flatpage_id=page.id, site_id=current_site.id)
        )
    # Create all relationships at once
    logger.info(f"creating {len(sites_relations)} sites relationships")
    ThroughModel.objects.bulk_create(sites_relations)


def createPredefinedCustomFlatPages(apps, deserialized_pages):
    BaseFlatPage = apps.get_model("flatpages", "FlatPage")
    CustomFlatPage = apps.get_model("pages", "FlatPage")

    for deserialized_page in deserialized_pages:
        base, custom = deserialized_page["base"], deserialized_page["custom"]
        logger.info(f"looking at  page url={base.url}")
        db_base = BaseFlatPage.objects.filter(url__iexact=base.url)
        if db_base.exists():
            pk = db_base.first().pk
            logger.info(f"found base with pk={pk}")
            db_custom = CustomFlatPage.objects.filter(pk=pk)
            if db_custom.exists():  # custom already exists, check if it was updated
                db_custom = db_custom.first()
                logger.info(f"found custom with pk={pk}")
                if (
                    db_custom.updated
                ):  # updated since last import, we can't safely update it
                    logger.info("updated since last import, we can't safely update it")
                    continue
                if (
                    db_custom.title != custom.title
                    or db_custom.content != custom.content
                    or db_custom.url != custom.url
                ):
                    db_custom.title = custom.title
                    db_custom.content = custom.content
                    db_custom.url = custom.url
                    db_custom.predefined = True
                    logger.info(
                        f"updating custom with info {db_custom.title} {db_custom.content} {db_custom.url} as predefined"
                    )
                    db_custom.save()
            else:  # custom doesn't exist, create it as predefined and use the base pk, updating db_base with base data
                createCustomFlatPage(
                    apps,
                    base,
                    predefined=custom.predefined,
                    updated=custom.updated,
                    pk=pk,
                )
        else:  # base (and thus custom) doesn't exist, create the custom will create the base. No pk here
            createCustomFlatPage(
                apps, base, predefined=custom.predefined, updated=custom.updated
            )


def createNonPredefinedCustomFlatPages(apps):
    """
    For each base FlatPage, if the corresponding custom FlatPage doesn't exist,
    create it with predefined=False and updated=True. This is used for the initial
    migration from the built-in FlatPage model to the custom model.
    Supposes predefined  custom FlatPages were already imported using createPredefinedCustomFlatPages().
    """
    BaseFlatPage = apps.get_model("flatpages", "FlatPage")
    CustomFlatPage = apps.get_model("pages", "FlatPage")
    for basePage in BaseFlatPage.objects.all():
        if not CustomFlatPage.objects.filter(pk=basePage.pk).exists():
            # CustomFlatPage doesn't exist, initial migration using the base pk
            createCustomFlatPage(
                apps, basePage, predefined=False, updated=True, pk=basePage.pk
            )


def migrateOrCreateCustomeFlatPages(apps, schema_editor):
    # remove constraints check on atomicity
    # Open and load the fixture file
    with open("pages/fixtures/predefined_flatpages.json") as fixture_file:
        deserialized = serializers.deserialize("json", fixture_file)
        base_pages = []
        custom_pages = []
        for item in deserialized:
            deserialized_obj = item.object
            if (
                deserialized_obj._meta.app_label == "flatpages"
                and deserialized_obj._meta.model_name == "flatpage"
            ):
                # this is a base page, just remember it for when we'll read the corresponding custom page
                base_pages.append(deserialized_obj)
            elif (
                deserialized_obj._meta.app_label == "pages"
                and deserialized_obj._meta.model_name == "flatpage"
            ):
                # this is a custom page, link it to the base
                bases = [page for page in base_pages if page.pk == deserialized_obj.pk]
                if bases:
                    custom_pages.append({"custom": deserialized_obj, "base": bases[0]})
                else:
                    raise ValueError(
                        f"Base flat page not found for page {deserialized_obj.pk}"
                    )
            else:
                raise ValueError(
                    f"Unknown object type {type(deserialized_obj)} when deserializing predefined_flatpages.json"
                )

    with schema_editor.connection.constraint_checks_disabled():
        with transaction.atomic():
            createPredefinedCustomFlatPages(apps, custom_pages)
            createNonPredefinedCustomFlatPages(apps)
        with transaction.atomic():
            createSitesRelationship(apps)


def reverseMigrateOrCreateCustomeFlatPages(apps, schema_editor):
    # Code to cancel loading if necessary
    CustomFlatPage = apps.get_model("pages", "FlatPage")
    # cancel all predefined non updated pages, they will be recreated on next migration
    CustomFlatPage.objects.filter(predefined=True, updated=False).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            migrateOrCreateCustomeFlatPages,
            reverse_code=reverseMigrateOrCreateCustomeFlatPages,
        ),
    ]
