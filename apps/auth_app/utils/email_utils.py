"""
Utilidades centralizadas para envío de correos electrónicos.
Incluye:
 - Envío de código de verificación (HTML)
 - Envío de restablecimiento de contraseña (HTML)
"""

import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


def send_email(subject: str, to_email: str, html_content: str, text_fallback: str = "") -> bool:
    """
    Envía un correo HTML con respaldo en texto plano.
    Esto evita que se detecte como spam y asegura compatibilidad.
    """
    from_email = settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER
    if not from_email:
        logger.error("No se ha configurado DEFAULT_FROM_EMAIL ni EMAIL_HOST_USER.")
        return False

    try:
        logger.debug(f"Enviando correo HTML a {to_email} desde {from_email}")

        send_mail(
            subject=subject,
            message=text_fallback or "Contenido HTML adjunto.",
            from_email=from_email,
            recipient_list=[to_email],
            html_message=html_content,   # <–– ESTO ES LO IMPORTANTE
            fail_silently=False,
        )

        logger.info(f"Correo enviado correctamente a {to_email}")
        return True

    except Exception as e:
        logger.error(f"Error al enviar correo a {to_email}: {e}")
        return False


def send_verification_email(to_email: str, code: str) -> bool:
    """Envía un correo HTML con el código de verificación de 6 dígitos."""
    subject = "Verificar tu cuenta para empezar a flechar"

    body_lines = [
        f"Tu código de verificación es: <strong>{code}</strong>",
        "Este código es válido por 10 minutos.",
        "Si no solicitaste este código, puedes ignorar este mensaje."
    ]

    html_content = build_email(subject, body_lines)

    text_fallback = (
        f"Tu código de verificación es: {code}\n"
        f"Válido por 10 minutos.\n"
        f"Si no lo solicitaste, ignora este mensaje."
    )

    return send_email(subject, to_email, html_content, text_fallback)


def send_password_reset_email(to_email: str, token: str) -> bool:
    """Envía un correo HTML con el token de recuperación de contraseña."""
    subject = "Recupera tu contraseña - cUPido"

    body_lines = [
        "Recibimos una solicitud para restablecer tu contraseña.",
        f"Tu token de recuperación es: <strong>{token}</strong>",
        "Este token es válido por 30 minutos.",
        "Si no solicitaste este cambio, ignora este mensaje."
    ]

    html_content = build_email(subject, body_lines)

    text_fallback = (
        f"Token de recuperación: {token}\n"
        f"Válido por 30 minutos.\n"
        f"Si no solicitaste el cambio, ignora este mensaje."
    )

    return send_email(subject, to_email, html_content, text_fallback)


def build_email(title: str, body_lines: list[str]) -> str:
    body_html = "".join(f"<li>{line}</li>" for line in body_lines)

    return f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title}</title>
</head>

<body style="font-family: 'Segoe UI', Helvetica, Arial, sans-serif; background:#f4f4f7; margin:0; padding:0;">
    <table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 0;">
        <tr>
            <td align="center">

                <table width="600" cellpadding="0" cellspacing="0"
                       style="background:#ffffff; border-radius:12px; overflow:hidden; box-shadow:0 4px 16px rgba(0,0,0,0.08);">

                    <tr>
                        <td>
                            <img src="https://i.postimg.cc/28hpQGnw/Pareja-Copas.png" alt="Banner" width="100%"
                                 style="display:block; max-height:220px; object-fit:cover;">
                        </td>
                    </tr>

                    <tr>
                        <td style="padding:30px 40px 10px 40px; text-align:center;">
                            <h1 style="margin:0; font-size:24px; font-weight:600; color:#333;">
                                {title}
                            </h1>
                        </td>
                    </tr>

                    <tr>
                        <td style="padding:0px 40px 20px 40px; font-size:15px; color:#555;">
                            <ul style="padding-left:20px; margin:0; line-height:1.6;">
                                {body_html}
                            </ul>
                        </td>
                    </tr>

                    <tr>
                        <td style="padding:25px 40px 35px 40px; text-align:center; border-top:1px solid #eee;">
                            <p style="margin:0; font-size:14px; color:#777;">
                                Atentamente,<br>
                                <strong>Equipo de cUPido ❤️</strong>
                            </p>
                            <p style="margin-top:10px; font-size:12px; color:#999;">
                                Este mensaje fue generado automáticamente.
                            </p>
                        </td>
                    </tr>

                </table>

            </td>
        </tr>
    </table>
</body>
</html>
"""
