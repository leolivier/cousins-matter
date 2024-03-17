from django.db.models.signals import post_save, post_delete
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Member
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def create_or_update_member(sender, instance, created, **kwargs):
    logger.info(f"user {instance.username}: post save member triggered")
    if created: # new user, see if we need to create his associated member
        #  if it does exist (match by email), just link them
        member = Member.objects.filter(email=instance.email).first()
        if member:
            logger.info(f"New user {instance.username}: linking existing member")
            member.account = instance
            member.managing_account = instance
            member.save()
        else:
            logger.info(f"New user {instance.username}: creating associated member")
            Member.objects.create(account=instance, 
                                  managing_account=instance,
                                  first_name=instance.first_name,
                                  last_name=instance.last_name,
                                  email = instance.email,
                            ).save()
    else: # existing user, update his member?
        logger.info(f"User {instance.username}: not updating member {instance.member.__str__()}")

@receiver(post_delete, sender=User)
def user_delete_member(sender, instance, **kwargs):
    logger.info(f"user {instance.username}: post delete user triggered")
    member = Member.objects.filter(account__id = instance.id)
    if member:
        member = member.first()
        logger.info(f"User {instance.username}: reseting member {member.__str__()} account")
        member.account = None
        member.save()
    member = Member.objects.filter(managing_account__id = instance.id)
    if member:
        member = member.first()
        logger.info(f"User {instance.username}: reseting member {member.__str__()} account")
        member.account = None
        member.save()

# kwargs = {
#     '{0}__{1}'.format('name', 'startswith'): 'A',
#     '{0}__{1}'.format('name', 'endswith'): 'Z'
# }

# Person.objects.filter(**kwargs)