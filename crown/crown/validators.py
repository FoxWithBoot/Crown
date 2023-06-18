
def check_public_or_author(user, obj):
    """Проверка на то, что страница либо опубликована, либо принадлежит пользователю"""
    if obj:
        if not obj.is_public and obj.author != user:
            return False
    return True
