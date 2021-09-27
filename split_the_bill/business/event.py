from split_the_bill.models import EventInvitation
from django.db.models import Sum


class EventBusiness:
    def __init__(self, event):
        self.event = event

    def remove_members(self, member_pks):
        self.event.members.remove(*member_pks)
        # After removing members, also remove invitations
        # so that removed members can be invited again
        EventInvitation.objects.filter(user__pk__in=member_pks).delete()

    def get_total_fund(self):
        result = self.event.transactions\
                           .transactions_to_fund()\
                           .aggregate(total_fund=Sum('amount'))
        return result['total_fund'] or 0

    def get_total_expense(self):
        result = self.event.transactions\
                           .expenses()\
                           .aggregate(total_expense=Sum('amount'))
        return result['total_expense'] or 0
