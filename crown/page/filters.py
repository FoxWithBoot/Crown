from django.db.models import Q
from django_filters import rest_framework as filters
from .models import Page


class PageFilter(filters.FilterSet):
    without_parent = filters.BooleanFilter(field_name='parent', lookup_expr='isnull', help_text="Без родителя?")
    in_other_space = filters.BooleanFilter(method='filter_in_other_space', help_text="Искать в чужих вселенных?")

    class Meta:
        model = Page
        fields = ['is_public', 'is_removed', 'parent__author']

    def filter_in_other_space(self, queryset, name, value):
        if value:
            return queryset.filter(Q(author=self.request.user) & ~Q(parent__author=self.request.user) & ~Q(parent=None))
        return queryset


