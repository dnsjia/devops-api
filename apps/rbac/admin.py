#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.

from django.contrib import admin
from apps.rbac.models import Role, Permission, Menu

admin.site.register(Role)
admin.site.register(Permission)
admin.site.register(Menu)