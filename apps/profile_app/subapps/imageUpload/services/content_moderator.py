"""
Servicio de moderación de contenido usando Sightengine.
Lógica de negocio: Validar que las imágenes no contengan contenido inapropiado
(desnudez, violencia, armas, drogas) antes de permitir su publicación.
Si el servicio falla, la imagen se acepta para no bloquear al usuario.
"""
import requests
from django.conf import settings
from typing import Tuple, Dict, Any
import io


class ContentModerator:
    """
    Moderador de contenido que usa Sightengine API para detectar
    contenido inapropiado en imágenes.
    """
    
    API_URL = "https://api.sightengine.com/1.0/check.json"
    
    # Umbrales de rechazo (si el score supera estos valores, se rechaza)
    THRESHOLDS = {
        'nudity': 0.7,      # Desnudez parcial o total
        'weapon': 0.5,      # Armas
        'alcohol': 0.7,     # Alcohol (más permisivo)
        'drugs': 0.5,       # Drogas
        'gore': 0.3,        # Gore/violencia gráfica (más estricto)
        'violence': 0.5,    # Violencia general
    }
    
    # Modelos a usar en Sightengine
    MODELS = "nudity-2.1,weapon,alcohol,recreational_drug,gore-2.0,violence"

    @classmethod
    def moderate_image(cls, image_file) -> Tuple[bool, str]:
        """
        Modera una imagen para detectar contenido inapropiado.
        
        Args:
            image_file: Archivo de imagen (file-like object)
            
        Returns:
            Tuple[bool, str]: (es_aceptable, mensaje)
            - Si es_aceptable es True, la imagen pasó la moderación
            - Si es False, el mensaje indica qué contenido fue detectado
            
        Lógica:
        - Si Sightengine falla o está caído, aceptar la imagen (fail-open)
        - Si detecta contenido inapropiado, rechazar con mensaje específico
        """
        api_user = getattr(settings, 'SIGHTENGINE_API_USER', None)
        api_secret = getattr(settings, 'SIGHTENGINE_API_SECRET', None)
        
        # Si no hay credenciales configuradas, aceptar la imagen
        if not api_user or not api_secret:
            print("[ContentModerator] Credenciales no configuradas, aceptando imagen")
            return True, "Moderación no configurada"
        
        try:
            # Preparar el archivo para envío
            image_file.seek(0)
            image_data = image_file.read()
            image_file.seek(0)
            
            # Llamar a Sightengine API
            response = requests.post(
                cls.API_URL,
                files={'media': ('image.jpg', io.BytesIO(image_data), 'image/jpeg')},
                data={
                    'api_user': api_user,
                    'api_secret': api_secret,
                    'models': cls.MODELS,
                },
                timeout=5  # Timeout de 5 segundos (optimizado de 10s)
            )
            
            if response.status_code != 200:
                # Error en la API, aceptar imagen (fail-open)
                print(f"[ContentModerator] Error API status {response.status_code}, aceptando imagen")
                return True, "Error en servicio de moderación"
            
            result = response.json()
            
            if result.get('status') != 'success':
                # Error en respuesta, aceptar imagen
                print(f"[ContentModerator] Respuesta no exitosa: {result}, aceptando imagen")
                return True, "Error en respuesta de moderación"
            
            # Analizar resultados
            return cls._analyze_results(result)
            
        except requests.exceptions.Timeout:
            print("[ContentModerator] Timeout en API, aceptando imagen")
            return True, "Timeout en moderación"
        except requests.exceptions.RequestException as e:
            print(f"[ContentModerator] Error de conexión: {e}, aceptando imagen")
            return True, "Error de conexión en moderación"
        except Exception as e:
            print(f"[ContentModerator] Error inesperado: {e}, aceptando imagen")
            return True, "Error inesperado en moderación"
    
    @classmethod
    def _analyze_results(cls, result: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Analiza los resultados de Sightengine y determina si la imagen es aceptable.
        """
        rejections = []
        
        # Verificar desnudez
        nudity = result.get('nudity', {})
        # Sightengine 2.1 usa diferentes campos para tipos de desnudez
        nudity_score = max(
            nudity.get('sexual_activity', 0),
            nudity.get('sexual_display', 0),
            nudity.get('erotica', 0),
            nudity.get('very_suggestive', 0),
            nudity.get('suggestive', 0) * 0.5,  # Suggestive es menos grave
        )
        if nudity_score > cls.THRESHOLDS['nudity']:
            rejections.append("contenido sexual o desnudez")
        
        # Verificar armas
        weapon = result.get('weapon', {})
        weapon_score = weapon.get('classes', {}).get('firearm', 0)
        knife_score = weapon.get('classes', {}).get('knife', 0)
        if weapon_score > cls.THRESHOLDS['weapon'] or knife_score > cls.THRESHOLDS['weapon']:
            rejections.append("armas")
        
        # Verificar alcohol
        alcohol = result.get('alcohol', {})
        if alcohol.get('prob', 0) > cls.THRESHOLDS['alcohol']:
            rejections.append("alcohol")
        
        # Verificar drogas
        drugs = result.get('recreational_drug', {})
        if drugs.get('prob', 0) > cls.THRESHOLDS['drugs']:
            rejections.append("drogas")
        
        # Verificar gore
        gore = result.get('gore', {})
        if gore.get('prob', 0) > cls.THRESHOLDS['gore']:
            rejections.append("contenido violento o gore")
        
        # Verificar violencia general
        violence = result.get('violence', {})
        if violence.get('prob', 0) > cls.THRESHOLDS['violence']:
            rejections.append("violencia")
        
        if rejections:
            # Mensaje técnico para logs
            log_message = f"Imagen rechazada por contener: {', '.join(rejections)}"
            print(f"[ContentModerator] {log_message}")
            
            # Mensaje amigable para el usuario
            user_message = cls._get_user_friendly_message(rejections)
            return False, user_message
        
        return True, "Imagen aprobada"
    
    @classmethod
    def _get_user_friendly_message(cls, rejections: list) -> str:
        """
        Genera un mensaje amigable para el usuario basado en el contenido detectado.
        Lógica: Mostrar un mensaje claro sin ser alarmista, indicando por qué se rechazó.
        """
        # Mapeo de términos técnicos a mensajes amigables
        friendly_terms = {
            'contenido sexual o desnudez': 'contenido inapropiado',
            'armas': 'armas o elementos peligrosos',
            'alcohol': 'bebidas alcohólicas',
            'drogas': 'sustancias prohibidas',
            'contenido violento o gore': 'contenido violento',
            'violencia': 'escenas de violencia',
        }
        
        friendly_rejections = [friendly_terms.get(r, r) for r in rejections]
        
        if len(friendly_rejections) == 1:
            return f"Esta imagen no puede ser publicada porque contiene {friendly_rejections[0]}. Por favor, sube una foto diferente."
        else:
            items = ', '.join(friendly_rejections[:-1]) + f" y {friendly_rejections[-1]}"
            return f"Esta imagen no puede ser publicada porque contiene {items}. Por favor, sube una foto diferente."
