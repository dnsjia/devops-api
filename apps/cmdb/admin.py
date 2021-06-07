#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.

from django.contrib import admin
from apps.cmdb.models import CloudAK, Server, Disk, EcsAuthSSH


# Register your models here.
@admin.register(CloudAK)
class CloudAKAdmin(admin.ModelAdmin):
    list_display = ['access_key', 'access_secret', 'active']
    list_display_links = ['access_key']


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ['hostname', 'zone_id', 'private_ip', 'public_ip', 'cpu', 'memory', 'network_type', 'os_name',
                    'instance_charge_type', 'status', 'expired_time']
    list_display_links = ['hostname', 'public_ip']
    list_filter = ['network_type', 'os_type', 'zone_id', 'instance_charge_type', 'status']
    search_fields = ['instance_id', 'hostname', 'private_ip', 'public_ip', 'mac_address']


@admin.register(Disk)
class DiskAdmin(admin.ModelAdmin):
    list_display = ['instance_id', 'disk_id', 'category', 'encrypted', 'expired_time', 'disk_charge_type', 'size', 'status'
                    , 'type', 'portable', 'zone_id']
    list_display_links = ['disk_id']
    list_filter = ['category', 'status', 'type', 'encrypted', 'delete_with_instance', 'disk_charge_type']
    search_fields = ['instance__instance_id', 'disk_id', 'serial_number', 'instance__hostname']


@admin.register(EcsAuthSSH)
class EcsAuthSSHAdmin(admin.ModelAdmin):
    list_display = ['type', 'username', 'password', 'key', 'port', 'server_type']
    list_display_links = ['type']