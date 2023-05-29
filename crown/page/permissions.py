from rest_framework.permissions import BasePermission, SAFE_METHODS


class OnlyAuthorIfPrivate(BasePermission):
    """Если приватно, то разрешено только автору, иначе всем."""
    message = "Доступ разрешен только автору."

    def has_object_permission(self, request, view, obj):
        if obj.is_public:
            return True
        if request.user == obj.author:
            return True
        return False
