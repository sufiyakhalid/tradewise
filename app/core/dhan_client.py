from dhanhq import dhanhq

from app.core.config import settings


def get_dhan_client():
    return dhanhq(settings.DHAN_CLIENT_ID, settings.DHAN_ACCESS_TOKEN)
