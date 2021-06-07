#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.

from django.contrib import admin

from apps.application.models import Diagnosis


# Register your models here.


@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ['name', 'ip', 'user_name', 'is_active']
    list_display_links = ['name', 'user_name']
    list_filter = ['name', 'ip', 'user_name', 'is_active']
    search_fields = ['name', 'ip', 'user_name']
