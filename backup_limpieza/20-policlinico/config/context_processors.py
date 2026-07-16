def grupos_usuario(request):
    """
    Agrega los grupos del usuario al contexto de templates
    """
    if request.user.is_authenticated:
        grupos = list(request.user.groups.values_list('name', flat=True))
        return {
            'user_groups': grupos,
            'es_doctor': 'doctores' in grupos,
            'es_recepcion': 'recepcion' in grupos,
            'es_farmacia': 'farmacia' in grupos,
            'es_laboratorio': 'laboratorio' in grupos,
            'es_administrador': 'administrador' in grupos,
            'es_super_user': request.user.is_superuser,
        }
    return {}
