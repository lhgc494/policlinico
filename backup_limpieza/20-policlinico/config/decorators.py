from django.http import HttpResponseForbidden
from functools import wraps
from django.shortcuts import redirect

def grupo_requerido(*nombres_grupos):
    """
    Decorador para verificar que el usuario pertenezca a al menos uno de los grupos
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Verificar si está en alguno de los grupos requeridos
            user_groups = request.user.groups.values_list('name', flat=True)
            
            for grupo in nombres_grupos:
                if grupo in user_groups:
                    return view_func(request, *args, **kwargs)
            
            # Si es superuser, permitir (opcional)
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            return HttpResponseForbidden("No tiene permiso para acceder a esta página")
        return _wrapped_view
    return decorator
