from allauth.socialaccount.models import SocialAccount
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=SocialAccount)
def update_avatar(**kwargs):
    if not kwargs['created']:
        return

    social_account = kwargs['instance']
    user = social_account.user

    extra_data = social_account.extra_data
    social_avatar_url = extra_data.get('picture', '')

    if user.social_avatar_url != social_avatar_url:
        user.social_avatar_url = social_avatar_url
        user.save()
