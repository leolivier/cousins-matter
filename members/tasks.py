from dataclasses import dataclass, field
import logging
import os
import random
import string
from typing import Literal
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils.text import slugify
from django.utils.translation import (
    gettext as _,
    activate as translation_activate,
    deactivate as translation_deactivate,
)
from django.core.files import File

from .models import (
    ALL_FIELD_NAMES,
    MEMBER_FIELD_NAMES,
    ADDRESS_FIELD_NAMES,
    Member,
    Family,
    Address,
)

logger = logging.getLogger(__name__)
random.seed()


def t(field: str) -> str:
    return ALL_FIELD_NAMES[field]


def generate_random_string(length: int) -> str:
    return "".join(random.choice(string.printable) for _ in range(length))


@dataclass
class MemberImportData:
    "Represent a task of an import of members"

    # current row
    row: dict[str, str] = None
    # the member linked to the current row
    current_member: Member = None
    # current member has been changed or updated
    status: Literal["created", "updated"] | None = None
    # indicates if the activation was managed for the current member
    activation_managed: bool = False
    # indicates if we have warned the user that even if user activation is requested,
    # members with a manager in the file won't be activated
    warned_on_activate_users: bool = False
    # list of warnings and errors collected during the import of the current member
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def set_created(self):
        self.status = self.status or "created"

    def set_updated(self):
        self.status = self.status or "updated"

    def is_created_or_updated(self):
        return self.status is not None

    def is_created(self):
        return self.status == "created"

    def is_updated(self):
        return self.status == "updated"


@dataclass
class ImportContext:
    "Represent the data of an import of members"

    # indicate if we should activate imported users
    activate_users: bool = False
    # number of created members
    created_num: int = 0
    # number of updated members
    updated_num: int = 0
    # number of rows processed
    rows_num: int = 0
    # default manager used when a user is inactive, has no manager defined in the file and has no
    # current manager. Set to connected user (the one who is importing the file).
    default_manager: Member = None
    group: str = ""  # id of the group of tasks
    lang: str = "en"  # language of the file

    def register(self):
        MEMBER_IMPORTS[self.group] = self

    def unregister(self):
        if self.group in MEMBER_IMPORTS:
            del MEMBER_IMPORTS[self.group]

    @staticmethod
    def get(group: str) -> "ImportContext | None":
        return MEMBER_IMPORTS.get(group)


# in memory cache of MemberImportData
MEMBER_IMPORTS: dict[str, ImportContext] = {}


def manage_avatar(row_data: MemberImportData):
    username = row_data.row[t("username")]
    avatar_file = row_data.row[t("avatar")]
    avatar = os.path.join(settings.AVATARS_DIR, avatar_file)
    # avatar not changed
    if row_data.current_member.avatar and row_data.current_member.avatar.path == avatar:
        return

    # avatar image must already exist
    if not default_storage.exists(avatar):
        row_data.warnings.append(
            _("Avatar not found: %(avatar)s for username %(username)s. Ignored...")
            % {"avatar": avatar, "username": username}
        )
    else:
        try:
            with open(avatar, "rb") as image_file:
                image = File(image_file)
                row_data.current_member.avatar.save(avatar_file, image)
                row_data.set_updated()
        except Exception as e:
            row_data.warnings.append(
                _(
                    "Error saving avatar (%(warning)s): %(avatar)s for username %(username)s. Ignored..."
                )
                % {"warning": e, "avatar": avatar, "username": username}
            )


def manage_family(row_data: MemberImportData):
    family_name = row_data.row[t("family")]
    if (
        not row_data.current_member.family
        or row_data.current_member.family.name != family_name
    ):
        row_data.current_member.family, _ = Family.objects.get_or_create(
            name=family_name
        )
        row_data.set_updated()


def get_valid_manager(
    default_manager: Member, row_data: MemberImportData, manager_username
):
    if not manager_username:
        raise ValueError("No manager provided")

    new_member_manager = Member.objects.filter(username=manager_username).first()
    warning = ""

    if not new_member_manager or not new_member_manager.is_active:
        # no manager found or manager is inactive, keep the current manager or use the default manager
        if row_data.current_member.member_manager:
            new_member_manager = row_data.current_member.member_manager
            warning = _("Keeping current manager.")
        else:
            new_member_manager = default_manager
            warning = _("Using your id...")

    if not new_member_manager:  # should never happen!
        row_data.warnings.append(
            _("Manager %(manager)s not found for member %(member)s.")
            % {"manager": manager_username, "member": row_data.current_member.full_name}
            + " "
            + warning
        )
    elif not new_member_manager.is_active:
        row_data.errors.append(
            _(
                "%(manager)s is inactive and cannot be used as manager for %(member)s. "
                "Activate it manually!"
            )
            % {"manager": manager_username, "member": row_data.current_member.full_name}
            + " "
            + warning
        )
    # print(f'new member manager for {self.current_member.username} = {new_member_manager.username}')
    return new_member_manager


def handle_no_manager_case(context: ImportContext, row_data: MemberImportData):
    if row_data.current_member.is_active:
        return
    if context.activate_users:
        row_data.current_member.is_active = True
        row_data.current_member.member_manager = None
        row_data.set_updated()
    elif row_data.current_member.member_manager:
        row_data.warnings.append(
            _(
                "No manager provided for member %(member)s although inactive. "
                "Keeping existing one (%(manager)s)..."
            )
            % {
                "member": row_data.current_member.full_name,
                "manager": row_data.current_member.member_manager.full_name,
            }
        )
    else:
        row_data.errors.append(
            _(
                "Inactive member %(member)s has no manager. Please provide one! "
                "Meanwhile, you will be used as manager"
            )
            % {"member": row_data.current_member.full_name}
        )
        row_data.current_member.member_manager = context.default_manager
        row_data.set_updated()


def handle_managed_by(context: ImportContext, row_data: MemberImportData):
    manager_username = row_data.row[t("managed_by")]
    if not manager_username:  # cell present but empty
        handle_no_manager_case(context, row_data)
        return

    new_member_manager = get_valid_manager(
        context.default_manager, row_data, manager_username
    )

    if row_data.current_member.member_manager != new_member_manager:
        row_data.current_member.member_manager = new_member_manager
        row_data.set_updated()

    if row_data.current_member.is_active:
        row_data.warnings.append(
            _(
                "Member %(member)s was active. Adding %(manager)s as manager inactivated him/her."
            )
            % {"member": row_data.current_member.full_name, "manager": manager_username}
        )
        row_data.current_member.is_active = False
        row_data.set_updated()

    if context.activate_users and not row_data.warned_on_activate_users:
        row_data.warned_on_activate_users = True
        row_data.warnings.append(
            _(
                "You requested to activate imported members. All members with a manager in the file "
                "will be ignored and won't be activated."
            )
        )
    row_data.activation_managed = True


def update_address(row_data: MemberImportData):
    address = {}
    for f in ADDRESS_FIELD_NAMES:
        trfield = t(f)
        if trfield in row_data.row:
            address[f] = row_data.row[trfield]
    # if len(address) == 5:   # we don't care if the address is incomplete
    if len(address) > 0:
        found = Address.objects.filter(**address).first()
        if found:
            if row_data.current_member.address != found:
                row_data.current_member.address = found
                row_data.set_updated()
        else:
            address = Address.objects.create(**address)
            address.save()
            row_data.current_member.address = address
            row_data.set_updated()


def update_member(context: ImportContext, row_data: MemberImportData):
    "update an existing member based on current row content"
    # for all member fields but username
    # if new value for this field, then override existing one
    for f in MEMBER_FIELD_NAMES:
        trfield = t(f)
        if trfield in row_data.row and row_data.row[trfield]:
            match f:
                case "username":
                    pass  # changing the username which is the user id does not make sense
                case "family":
                    manage_family(row_data)
                case "avatar":
                    manage_avatar(row_data)
                case "managed_by":
                    handle_managed_by(context, row_data)
                case _:
                    if row_data.current_member.__dict__[f] != row_data.row[trfield]:
                        setattr(row_data.current_member, f, row_data.row[trfield])
                        row_data.set_updated()


def create_member(context: ImportContext, row_data: MemberImportData):
    "create new member based on current row content."
    row_data.current_member = Member(is_active=False)
    row_data.set_created()
    # print(f"newly created member is active:{member.is_active}")
    for f in MEMBER_FIELD_NAMES:
        trfield = t(f)
        if trfield in row_data.row and row_data.row[trfield]:
            match f:
                case "family":
                    manage_family(row_data)
                case "managed_by":
                    handle_managed_by(context, row_data)
                case "avatar":
                    manage_avatar(row_data)
                case _:
                    setattr(row_data.current_member, f, row_data.row[trfield])

    row_data.current_member.password = generate_random_string(16)


def import_row(context: ImportContext, csv_row: dict):
    if context.lang:
        translation_activate(context.lang)
    logger.debug(
        f"start effectively importing row for username {csv_row[t('username')]}. lang: {context.lang}"
    )
    # normalize username using slugify
    csv_row[t("username")] = slugify(csv_row[t("username")])
    # search for an existing member with this username
    current_member = Member.objects.filter(username=csv_row[t("username")]).first()
    row_data = MemberImportData(row=csv_row, current_member=current_member)
    if current_member:  # found, update it
        logger.debug(f"found member: {current_member}, updating it")
        update_member(context, row_data)
    else:  # not found, create it
        logger.debug("Member not found, creating it")
        create_member(context, row_data)

    if (
        not row_data.activation_managed
    ):  # no "managed_by" column in the file or not filled for that member
        handle_no_manager_case(context, row_data)

  update_address(row_data)

    if row_data.is_created_or_updated():
        logger.debug(f"Saving member {row_data.current_member.__dict__}")
        row_data.current_member.save()

    if context.lang:
        translation_deactivate()
    return row_data  # this will the result retrieved by result_group
