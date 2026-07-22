from django.contrib.auth.views import LoginView
from django.shortcuts import redirect

class CustomLoginView(LoginView):
    def get_success_url(self):
        user = self.request.user

        if user.groups.filter(name='Administrador').exists():
            return '/admin/'
        elif user.groups.filter(name='Recepcionista').exists():
            return '/pacientes/'
        elif user.groups.filter(name='Medico').exists():
            return '/medico/'
        else:
            return '/'

