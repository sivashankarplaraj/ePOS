from django.conf import settings

def app_version(request):
    """Expose application version to all templates as APP_VERSION.

    Source of truth: settings.APP_VERSION (loaded from VERSION file or env var).
    """
    return {
        'APP_VERSION': getattr(settings, 'APP_VERSION', 'dev')
    }
