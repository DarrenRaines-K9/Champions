from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self) -> None:
        import sentry_sdk
        from django.conf import settings
        from sentry_sdk.integrations.django import DjangoIntegration

        from core.logging import configure_logging

        sentry_dsn = getattr(settings, "SENTRY_DSN", "")
        if sentry_dsn:
            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[DjangoIntegration()],
                traces_sample_rate=0.1 if not settings.DEBUG else 1.0,
                send_default_pii=False,
            )

        configure_logging(
            debug=settings.DEBUG,
            json=not settings.DEBUG,
            sentry_dsn=sentry_dsn,
        )
