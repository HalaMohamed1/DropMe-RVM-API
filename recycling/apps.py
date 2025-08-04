from django.apps import AppConfig

class RecyclingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recycling'
    
    def ready(self):
        # Import signals if you add any
        pass
