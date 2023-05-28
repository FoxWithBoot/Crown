
def check_public_or_author(user, page):
    """Проверка на то, что страница либо опубликована, либо принадлежит пользователю"""
    if page:
        if not page.is_public and page.author != user:
            return False
    return True
