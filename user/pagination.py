from rest_framework.pagination import LimitOffsetPagination


class UserSearchPagination(LimitOffsetPagination):
    default_limit = 10
