from django.apps import AppConfig





class Digital360ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'digital360Api'

    def ready(self):
        import digital360Api.signals