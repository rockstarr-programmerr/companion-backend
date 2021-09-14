from split_the_bill.models import EventInvitation


def remove_members(event, member_pks):
    event.members.remove(*member_pks)

    # After removing members, also remove invitations
    # so that removed members can be invited again
    EventInvitation.objects.filter(user__pk__in=member_pks).delete()
