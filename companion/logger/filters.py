import logging

def downgrade_host_not_allowed_error(record):
    if record.name == 'django.security.DisallowedHost':
        record.levelno = logging.WARNING
        record.levelname = logging.getLevelName(record.levelno)
    return True
