
def get_parent_page(page):
    if page.parent:
        get_parent_page(page.parent)
    return page
    # if page.author == user or page.is_public:
    #     return page
