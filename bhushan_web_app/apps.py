from django.apps import AppConfig


class BhushanWebAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bhushan_web_app'
    verbose_name = 'Products' 

    def ready(self):
        import bhushan_web_app.signals  
            