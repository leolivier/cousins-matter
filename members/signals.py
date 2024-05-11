from django.db.models.signals import post_save, post_delete
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Member
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_creates_member(sender, instance, created, **kwargs):
    logger.debug(f"user {instance.username}: post save user triggered for Member")
    if created:  # new user, see if we need to create his associated member
        if Member.objects.filter(account__id=instance.id).exists():
            logger.debug(f"User {instance.username} already has an associated member.")
        else:
            logger.debug(f"New user {instance.username}: creating associated member")
            Member.objects.create(account=instance).save()
    else:  # existing user
        if instance.is_active:
            member = Member.objects.get(account__id=instance.id)
            if member.managing_account != instance:
                member.managing_account = instance
                member.save()
                logger.debug(f"User {instance.username} changed, updating managing account")
        else:
            logger.debug(f"User {instance.username} changed, nothing to change on Member")


@receiver(post_delete, sender=User)
def delete_user_deletes_member(sender, instance, **kwargs):
    logger.debug(f"user {instance.username}: post delete user triggered")
    # delete associated member (should be done by delete cascade!)
    member = Member.objects.filter(account__id=instance.id)
    if member.exists():
        logger.debug(f"User {instance.username} deleted: deleting associated member.")
        member.first().delete()
    # if managing account is deleted, associate managed members to first admin
    managed_members = Member.objects.filter(managing_account__id=instance.id)
    admin = User.objects.filter(is_superuser=True).first()
    for member in managed_members:
        logger.debug(f'''
                     User {instance.username} deleted:
                     associating managed member {member.str()} to {admin.username} managing account
                     ''')
        member.managing_account = admin
        member.save()

# not enouch information to create a user: must done through the UI
# @receiver(post_save, sender=Member)
# def create_member_creates_user(sender, instance, created, **kwargs):
#     logger.debug(f"member {instance.id}: post save member triggered for User")
#     if created: # new member, see if we need to create his associated user
#         if User.objects.filter(id = instance.account.id):
#             logger.debug(f"Member {instance.id} already has an associated user.")
#         else:
#             logger.debug(f"New member: creating associated user")
#             account = User.objects.create_user(username=instance.account.username,
#                                      password=<PASSWORD>,
#                                      is_active=False)


@receiver(post_delete, sender=Member)
def delete_member_deletes_user(sender, instance, **kwargs):
    logger.debug(f"member {instance.id}: post delete member triggered")
    # delete associated user (should be done by delete cascade!)
    user = User.objects.filter(id=instance.account.id)
    if user.exists():
        logger.debug(f"Member {instance.id} deleted: deleting associated user.")
        user.first().delete()
