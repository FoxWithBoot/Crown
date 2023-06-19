from django.db.models import F, Q

from road.models import Road


def get_list_public_authors_in_space(page, user):
    parent_page = page.get_root()
    authors_in_space = parent_page.get_descendants(include_self=True)
    if user.is_anonymous:
        authors_in_space = authors_in_space.filter(is_public=True).order_by()
    else:
        authors_in_space = authors_in_space.filter(Q(is_public=True) | Q(author=user)).order_by()
    authors_in_space = authors_in_space.values_list('author__id', 'author__username', named=True).distinct()
    authors_in_space = authors_in_space.values(id=F('author__id'), username=F('author__username'))
    return authors_in_space


def get_list_public_authors_in_page_roads(page, user, parent_road=None):
    if not parent_road:
        parent_road = Road.objects.get(page=page, parent=None)
    authors_in_page = parent_road.get_descendants(include_self=True)
    if user.is_anonymous:
        authors_in_page = authors_in_page.filter(is_public=True).order_by()
    else:
        authors_in_page = authors_in_page.filter(Q(is_public=True) | Q(author=user)).order_by()
    authors_in_page = authors_in_page.values_list('author__id', 'author__username', named=True).distinct()
    authors_in_page = authors_in_page.values(id=F('author__id'), username=F('author__username'))
    return authors_in_page


