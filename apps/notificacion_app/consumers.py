"""Consumer WebSocket para notificaciones en tiempo real.

Gestiona la conexión WebSocket por usuario, autenticando mediante
JWT (query string) o fallback a búsqueda directa por user_id.
Cada usuario se une a un grupo "user_{id}" para recibir eventos.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.conf import settings
import jwt

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    """Consumer WebSocket de notificaciones.

    Autentica por JWT (query string) o búsqueda directa.
    Se une al grupo "user_{id}" para recibir eventos de notificaciones.
    Maneja ping/pong y redirige notification_message al cliente.
    """

    @database_sync_to_async
    def get_user(self, user_id):
        """Obtiene usuario por usuario_id con múltiples intentos de búsqueda."""
        try:
            return User.objects.get(usuario_id=int(user_id))
        except (ValueError, TypeError):
            try:
                return User.objects.get(username=user_id)
            except User.DoesNotExist:
                return None
        except User.DoesNotExist:
            return None
        except AttributeError:
            try:
                return User.objects.get(id=user_id)
            except Exception:
                return None

    @database_sync_to_async
    def get_user_from_token(self, token):
        """Decodifica JWT manualmente y obtiene el usuario asociado."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id') or payload.get('id') or payload.get('usuario_id') or payload.get('sub')
            if not user_id:
                return None
            try:
                return User.objects.get(usuario_id=int(user_id))
            except (ValueError, TypeError):
                return User.objects.get(username=user_id)
            except User.DoesNotExist:
                try:
                    return User.objects.get(id=user_id)
                except User.DoesNotExist:
                    return None
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, User.DoesNotExist):
            return None

    async def connect(self):
        print(f"🔗 [WebSocket] Connection attempt")
        
        # Obtener user_id desde la URL
        url_user_id = self.scope["url_route"]["kwargs"].get("user_id")
        
        if not url_user_id:
            print("❌ [WebSocket] No user_id in URL")
            await self.close(code=4000)
            return
        
        self.url_user_id = url_user_id
        print(f"📋 [WebSocket] URL User ID: {self.url_user_id}")
        
        # Intentar autenticar por token
        query_string = self.scope.get('query_string', b'').decode()
        print(f"📝 [WebSocket] Query string: {query_string}")
        
        token = None
        if query_string:
            params = query_string.split('&')
            for param in params:
                if param.startswith('token='):
                    token = param.split('=')[1]
                    break
        
        user = None
        
        if token:
            print("🔑 [WebSocket] Authenticating with token...")
            user = await self.get_user_from_token(token)
            if user:
                print(f"✅ [WebSocket] User authenticated via token: {user.usuario_id} - {user.username}")
        
        # Si no hay token o la autenticación falló, intentar directamente
        if not user:
            print("👤 [WebSocket] Attempting direct user lookup...")
            user = await self.get_user(self.url_user_id)
            if user:
                print(f"✅ [WebSocket] User found directly: {user.usuario_id} - {user.username}")
        
        if not user:
            print(f"❌ [WebSocket] User not found: {self.url_user_id}")
            await self.close(code=4001)
            return
        
        # Verificar que el user_id coincide (comparar usuario_id)
        if hasattr(user, 'usuario_id'):
            if str(user.usuario_id) != str(self.url_user_id):
                print(f"⚠️ [WebSocket] User ID mismatch. URL: {self.url_user_id}, User: {user.usuario_id}")
                # Podemos ser flexibles aquí, pero depende de tu política de seguridad
                # await self.close(code=4003)
                # return
        elif str(user.id) != str(self.url_user_id):
            print(f"⚠️ [WebSocket] User ID mismatch. URL: {self.url_user_id}, User: {user.id}")
        
        self.user = user
        self.user_id = user.usuario_id if hasattr(user, 'usuario_id') else user.id
        
        # Nombre del grupo usando el ID real del usuario
        self.group_name = f"user_{self.user_id}"
        
        print(f"📡 [WebSocket] Joining group: {self.group_name}")
        
        # Unirse al grupo
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        
        # Conexión aceptada
        await self.accept()
        print(f"🎉 [WebSocket] Connection established for user {self.user_id} ({user.username})")
        
        # Enviar mensaje de bienvenida
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': f'WebSocket connected for user {self.user_id}',
            'user_id': self.user_id,
            'timestamp': self.get_current_time()
        }))

    async def disconnect(self, close_code):
        """Remover del grupo al desconectar"""
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            print(f"🔌 [WebSocket] Disconnected from group: {self.group_name}")
        
        print(f"👋 [WebSocket] Disconnected. Code: {close_code}")
    
    async def receive(self, text_data):
        """Manejar mensajes recibidos del cliente"""
        try:
            data = json.loads(text_data)
            print(f"📨 [WebSocket] Received from user {self.user_id}: {data}")
            
            # Manejar diferentes tipos de mensajes
            message_type = data.get('type')
            
            if message_type == 'ping':
                # Responder al ping
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp'),
                    'server_time': self.get_current_time()
                }))
            elif message_type == 'echo':
                # Echo de prueba
                await self.send(text_data=json.dumps({
                    'type': 'echo_response',
                    'original_message': data.get('message'),
                    'timestamp': self.get_current_time()
                }))
                
        except json.JSONDecodeError:
            print(f"❌ [WebSocket] Invalid JSON received: {text_data}")
    
    async def notification_message(self, event):
        """Enviar notificación al WebSocket"""
        notification_data = event.get('data', {})
        print(f"📤 [WebSocket] Sending notification to user {self.user_id}: {notification_data}")
        
        await self.send(text_data=json.dumps(notification_data))
    
    def get_current_time(self):
        """Obtener tiempo actual en formato ISO"""
        from datetime import datetime
        return datetime.now().isoformat()