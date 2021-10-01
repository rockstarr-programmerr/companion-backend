from .filters import downgrade_host_not_allowed_error


def logging_config(base_dir):
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '{levelname} {asctime} {module} {message}',
                'style': '{',
            },
            'django.server': {
                '()': 'django.utils.log.ServerFormatter',
                'format': '[{server_time}] {message}',
                'style': '{',
            },
        },
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse',
            },
            'require_debug_true': {
                '()': 'django.utils.log.RequireDebugTrue',
            },
            'downgrade_host_not_allowed_error': {
                '()': 'django.utils.log.CallbackFilter',
                'callback': downgrade_host_not_allowed_error,
            },
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'filters': ['require_debug_true'],
            },
            'django.server': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'django.server',
            },
            'file_info': {
                'level': 'INFO',
                'class': 'logging.FileHandler',
                'filename': base_dir / 'logs/info.log',
                'filters': ['downgrade_host_not_allowed_error', 'require_debug_false'],
                'formatter': 'verbose',
            },
            'file_warning': {
                'level': 'WARNING',
                'class': 'logging.FileHandler',
                'filename': base_dir / 'logs/warning.log',
                'filters': ['downgrade_host_not_allowed_error', 'require_debug_false'],
                'formatter': 'verbose',
            },
            'file_error': {
                'level': 'ERROR',
                'class': 'logging.FileHandler',
                'filename': base_dir / 'logs/error.log',
                'filters': ['downgrade_host_not_allowed_error', 'require_debug_false'],
                'formatter': 'verbose',
            },
            'mail_admins': {
                'level': 'ERROR',
                'class': 'django.utils.log.AdminEmailHandler',
                'filters': ['downgrade_host_not_allowed_error', 'require_debug_false'],
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console', 'file_info', 'file_warning', 'file_error', 'mail_admins'],
                'level': 'INFO',
            },
            'django.server': {
                'handlers': ['django.server'],
                'level': 'INFO',
                'propagate': False,
            },
            'companion': {
                'handlers': ['console', 'file_info', 'file_warning', 'file_error', 'mail_admins'],
                'level': 'INFO',
            },
            'split_the_bill': {
                'handlers': ['console', 'file_info', 'file_warning', 'file_error', 'mail_admins'],
                'level': 'INFO',
            },
            'user': {
                'handlers': ['console', 'file_info', 'file_warning', 'file_error', 'mail_admins'],
                'level': 'INFO',
            },
        }
    }
