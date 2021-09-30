from split_the_bill.models import EventInvitation


class EventBusiness:
    def __init__(self, event):
        self.event = event

    def remove_members(self, member_pks):
        self.event.members.remove(*member_pks)
        # After removing members, also remove invitations
        # so that removed members can be invited again
        EventInvitation.objects.filter(user__pk__in=member_pks).delete()

    def get_total_fund(self):
        result = self.event.transactions.total_fund()
        return result['total_fund']

    def get_total_expense(self):
        result = self.event.transactions.total_expense()
        return result['total_expense']
