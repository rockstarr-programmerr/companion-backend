from django.utils.translation import gettext_lazy as _, ngettext


_('No active account found with the given credentials')
_('This password is entirely numeric.')
ngettext(
    "This password is too short. It must contain at least %(min_length)d character.",
    "This password is too short. It must contain at least %(min_length)d characters.",
    8  # just a random number
)
