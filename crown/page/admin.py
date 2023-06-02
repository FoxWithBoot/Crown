from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from page.models import Page

admin.site.register(Page, MPTTModelAdmin)

