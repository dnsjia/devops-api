


https://django-request-id.readthedocs.io/en/latest/
- pip install django-request-id
```
LOGGING= {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_id": {
            "()": "request_id.logging.RequestIdFilter"
        }
    },
    "formatters": {
        "console": {
            "format": "%(asctime)s - %(levelname)-5s [%(name)s] request_id=%(request_id)s %(message)s",
            "datefmt": "%H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "filters": ["request_id"],
            "class": "logging.StreamHandler",
            "formatter": "console"
        }
    },
    "loggers": {
        "": {
            "level": "DEBUG",
            "handlers": ["console"]
        }
    }
}
```

https://github.com/nigma/django-request-id

https://github.com/dabapps/django-log-request-id

https://www.jianshu.com/p/5e103e1eb017