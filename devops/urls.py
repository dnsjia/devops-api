"""devops URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.views import static
from django.views.static import serve
from django.urls import path, include
from rest_framework.documentation import include_docs_urls

from api.views.download import DownLoadFile
from devops import settings
admin.site.site_header = "小飞猪运维管理后台"
admin.site.site_title = "Pigs Admin Portal"
admin.site.index_title = "Welcome to Pigs Operation Portal"

urlpatterns = [
    path('oa/', admin.site.urls),
    path('api/', include('api.urls')),
    path('rbac/', include('rbac.urls')),
    path('k8s/', include('k8s.urls')),
    path('case/', include('auto_case.urls')),
    url(r'^download/files/es/(.*).json$', DownLoadFile.as_view(), name='downloa_file'),
    url(r'files/(?P<path>.*)', serve, {'document_root': settings.MEDIA_ROOT}),
    url(r'caseimg/(?P<path>.*)', serve, {'document_root': settings.CASE_IMG_ROOT}),
    url(r'^static/(?P<path>.*)$', static.serve,{'document_root': settings.STATIC_ROOT}, name='static'),

]
