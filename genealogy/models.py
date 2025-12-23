from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from datetime import date


class Person(models.Model):
    SEX_CHOICES = [
        ("M", _("Male")),
        ("F", _("Female")),
        ("O", _("Other")),
    ]

    member = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="genealogy_person",
        verbose_name=_("Linked Member"),
    )

    first_name = models.CharField(_("First Name"), max_length=150)
    last_name = models.CharField(_("Last Name"), max_length=150)
    sex = models.CharField(_("Gender"), max_length=1, choices=SEX_CHOICES, default="O")

    birth_date = models.DateField(_("Birth Date"), null=True, blank=True)
    birth_place = models.CharField(_("Birth Place"), max_length=255, blank=True)

    death_date = models.DateField(_("Death Date"), null=True, blank=True)
    death_place = models.CharField(_("Death Place"), max_length=255, blank=True)

    notes = models.TextField(_("Notes"), blank=True)
    gedcom_id = models.CharField(
        "GEDCOM ID", max_length=50, blank=True, unique=True, null=True
    )

    child_of_family = models.ForeignKey(
        "Family",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("Child of Family"),
    )

    class Meta:
        verbose_name = _("Person")
        verbose_name_plural = _("People")
        indexes = [
            models.Index(fields=["last_name"]),
            models.Index(fields=["birth_date"]),
        ]
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        if not self.birth_date:
            return None
        end_date = self.death_date or date.today()
        return (
            end_date.year
            - self.birth_date.year
            - (
                (end_date.month, end_date.day)
                < (self.birth_date.month, self.birth_date.day)
            )
        )

    @property
    def gender_icon(self):
        return {
            "M": "gender-male",
            "F": "gender-female",
            "O": "genderless",
        }.get(self.sex, "question")

    def get_partners(self):
        """Returns a list of partners from all unions."""
        partners = []
        # As partner1
        for family in self.unions_as_p1.all():
            if family.partner2:
                partners.append(family.partner2)
        # As partner2
        for family in self.unions_as_p2.all():
            if family.partner1:
                partners.append(family.partner1)
        return partners


class Family(models.Model):
    UNION_TYPES = [
        ("MARR", _("Marriage")),
        ("CIVI", _("Civil union")),
        ("COHA", _("Cohabitation")),
        ("OTHE", _("Other")),
    ]

    partner1 = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="unions_as_p1",
        verbose_name=_("Partner 1"),
        null=True,
        blank=True,
    )
    partner2 = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="unions_as_p2",
        verbose_name=_("Partner 2"),
        null=True,
        blank=True,
    )

    union_type = models.CharField(
        _("Union Type"), max_length=4, choices=UNION_TYPES, default="MARR"
    )
    union_date = models.DateField(_("Union Date"), null=True, blank=True)
    union_place = models.CharField(_("Union Place"), max_length=255, blank=True)

    separation_date = models.DateField(_("Separation Date"), null=True, blank=True)

    class Meta:
        verbose_name = _("Family")
        verbose_name_plural = _("Families")

    def __str__(self):
        p1 = str(self.partner1) if self.partner1 else "?"
        p2 = str(self.partner2) if self.partner2 else "?"
        return f"{p1} & {p2}"
