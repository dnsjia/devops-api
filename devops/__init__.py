import pymysql
# 解决pymysql 版本报错问题
pymysql.version_info = (1, 3, 13, "final", 0)

pymysql.install_as_MySQLdb()

from .celery import app as celery_app

__all__ = ['celery_app']