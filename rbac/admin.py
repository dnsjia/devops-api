from django.contrib import admin
from rbac.models import *

admin.site.register(Role)
admin.site.register(Permission)
admin.site.register(Menu)