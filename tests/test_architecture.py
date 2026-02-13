import sys
import pkgutil
import pytest

# Definimos las capas prohibidas
def test_infrastructure_cannot_import_presentation():
    """
    Regla de Oro: La infraestructura NUNCA debe saber que existe la UI.
    Esto evita que el Ghost Lock falle por dependencias circulares.
    """
    import src.infrastructure.secrets_manager as sm
    
    # Buscamos si 'presentation' aparece en los módulos cargados por infrastructure
    modules = [m for m in sys.modules if 'src.presentation' in m]
    
    assert len(modules) == 0, f"VIOLACIÓN DE ARQUITECTURA: Se encontraron módulos de UI en la capa de datos: {modules}"

def test_domain_is_independent():
    """
    El Dominio debe ser puro. Verificamos que al importar mensajes,
    no se arrastren dependencias de infraestructura por error.
    """
    # Limpiamos rastro de módulos previos para una prueba limpia
    for m in list(sys.modules.keys()):
        if 'src.infrastructure' in m or 'src.presentation' in m:
            del sys.modules[m]

    import src.domain.messages as msg
    
    # Ahora verificamos si el import de mensajes provocó la carga de infra
    forbidden = [m for m in sys.modules if 'src.infrastructure' in m]
    
    assert len(forbidden) == 0, f"CONTAMINACIÓN DETECTADA: El dominio cargó {forbidden}"