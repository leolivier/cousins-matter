from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _


class MemberManager(BaseUserManager):
    """
    Member model manager where first_name, last_name are mandatory
    """

    def create_member(
        self, username, email, password, first_name, last_name, **extra_fields
    ):
        """
        Create and save a user with the given username, email, password, first_name and last_name.
        """
        if not username:
            raise ValueError(_("The username must be set"))

        extra_fields.setdefault("is_active", False)

        if email:
            email = self.normalize_email(email)
        user = self.model(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            **extra_fields,
        )
        user.set_password(password)
        user.save()
        return user

    async def acreate_member(
        self, username, email, password, first_name, last_name, **extra_fields
    ):
        """
        Async version of create_member
        """
        if not username:
            raise ValueError(_("The username must be set"))

        extra_fields.setdefault("is_active", False)

        if email:
            email = self.normalize_email(email)
        user = self.model(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            **extra_fields,
        )
        user.set_password(password)
        await user.asave()
        return user

    def create_superuser(
        self, username, email, password, first_name, last_name, **extra_fields
    ):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        return self.create_member(
            username, email, password, first_name, last_name, **extra_fields
        )

    def alive(self):
        return self.get_queryset().filter(is_dead=False)
