from rest_framework.pagination import PageNumberPagination


class UserPagination(PageNumberPagination):
    page_size_query_param = 'limit'