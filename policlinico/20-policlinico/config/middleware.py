from django.utils.deprecation import MiddlewareMixin

class NoCacheMiddleware(MiddlewareMixin):
    """
    Middleware para prevenir el cache en páginas que requieren autenticación
    """
    
    def process_response(self, request, response):
        # Si el usuario está autenticado, agregar headers anti-cache
        if request.user.is_authenticated:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        # Para TODAS las respuestas, prevenir cache (más seguro para tu caso)
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        return response
