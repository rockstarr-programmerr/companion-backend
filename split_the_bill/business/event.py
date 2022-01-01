from copy import copy

from django.utils.functional import cached_property

from split_the_bill.models import EventInvitation, Transaction


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


class SplitTheBillBusiness:
    def __init__(self, event):
        self.event = event

    @cached_property
    def members(self):
        return self.get_members()

    @cached_property
    def transactions(self):
        return self.get_transactions()

    def get_members(self):
        return list(self.event.members.all())

    def get_transactions(self):
        return list(self.event.transactions.all())

    def settle(self, tolerance=1000):
        cash_flows = self.get_cash_flows()
        minimized_cash_flows = self.minimize_cash_flows(cash_flows, tolerance)
        return minimized_cash_flows

    def get_cash_flows(self):
        cash_flows = []
        fund = _Fund(self.event.creator)  # For now, creator of event is also fund holder
        expense_per_member = self.get_expense_per_member()

        for member in self.members:
            net_amount = self.get_net_amount(member)
            amount_diff = expense_per_member - net_amount

            if amount_diff > 0:
                cash_flow = _CashFlow(member, fund.holder, amount_diff)
                cash_flows.append(cash_flow)
            elif amount_diff < 0:
                cash_flow = _CashFlow(fund.holder, member, -amount_diff)
                cash_flows.append(cash_flow)

        return cash_flows

    def minimize_cash_flows(self, cash_flows, tolerance):
        minimized_cash_flows = []

        members = copy(self.members)
        while len(members) > 1:  # If there's only 1 member left, there's nothing to settle anymore
            # Get net amount for each member (net amount = amount to receive - amount to pay)
            net_amounts = {member: 0 for member in members}
            for cash_flow in cash_flows:
                if cash_flow.from_user in net_amounts:
                    net_amounts[cash_flow.from_user] -= cash_flow.amount
                if cash_flow.to_user in net_amounts:
                    net_amounts[cash_flow.to_user] += cash_flow.amount

            # If all members' `net_amount` is 0, there's nothing to settle
            if all(amount == 0 for amount in net_amounts.values()):
                break

            # Find biggest creditor and debtor
            biggest_credit = 0
            biggest_debit = 0
            biggest_creditor = None
            biggest_debtor = None
            for member, amount in net_amounts.items():
                if amount >= biggest_credit:
                    biggest_creditor = member
                    biggest_credit = amount
                elif amount <= biggest_debit:
                    biggest_debtor = member
                    biggest_debit = amount

            # Settle for either the `biggest_creditor`, or the `biggest_debtor`,
            # depends on which amount of credit/debt is smaller
            if abs(biggest_credit) < abs(biggest_debit):
                settled_member = biggest_creditor
                settle_amount = biggest_credit
            else:
                settled_member = biggest_debtor
                settle_amount = -biggest_debit

            if tolerance:
                settle_amount = settle_amount - (settle_amount % tolerance)
            new_cash_flow = _CashFlow(biggest_debtor, biggest_creditor, settle_amount)
            minimized_cash_flows.append(new_cash_flow)

            # Remove `settled_member` from list of `members` before starting next iteration
            for index, member in enumerate(members):
                if member == settled_member:
                    break
            members.pop(index)

        return minimized_cash_flows

    def get_expense_per_member(self):
        expense_per_member = self.get_total_expense() / self.get_member_count()
        return expense_per_member

    def get_total_expense(self):
        return sum(
            transaction.amount
            for transaction in self.transactions
            if self.is_expense(transaction)
        )

    def get_member_count(self):
        return len(self.members)

    def get_net_amount(self, member):
        net_amount = 0
        for transaction in self.transactions:
            if transaction.from_user == member:
                net_amount += transaction.amount
            elif transaction.to_user == member:
                net_amount -= transaction.amount
        return net_amount

    @staticmethod
    def is_expense(transaction):
        return transaction.transaction_type in [
            Transaction.Types.USER_EXPENSE,
            Transaction.Types.FUND_EXPENSE
        ]


class _CashFlow:
    def __init__(self, from_user, to_user, amount):
        self.from_user = from_user
        self.to_user = to_user
        self.amount = amount


class _Fund:
    def __init__(self, holder):
        self.holder = holder
