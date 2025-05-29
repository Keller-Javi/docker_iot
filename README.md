# Telegram Bot + MQTT para Control de Raspberry Pi Pico

Este proyecto implementa un bot de Telegram que permite monitorear y controlar remotamente una Raspberry Pi Pico mediante mensajes MQTT cifrados (MQTTS). Está pensado para ser utilizado junto con el proyecto [Raspberry-Pi-Pico](https://github.com/Keller-Javi/Raspberry-Pi-Pico), que implementa un termostato en la Pico W con MicroPython.

Este bot facilita la interacción con el termostato desde Telegram, permitiendo modificar parámetros como el setpoint, el periodo de sensado, o el modo de funcionamiento, y recibir información del estado actual del dispositivo.

## Funcionalidades

- Consulta de temperatura y humedad actual.
- Cambio del setpoint de temperatura.
- Control del relé (modo manual o automático).
- Modificación del periodo de sensado.
- Activación de un destello LED.
- Consulta de la configuración actual del dispositivo.
- Acceso limitado a usuarios autorizados.

## Variables de entorno necesarias

Asegúrate de definir las siguientes variables en tu entorno o en un archivo `.env`:

```bash
TB_TOKEN=                # Token del bot de Telegram
TB_AUTORIZADOS=          # Lista de IDs de usuarios autorizados separados por coma (ejemplo: 123456789,987654321)
SERVIDOR=                # Dirección del servidor MQTT
PUERTO_MQTTS=            # Puerto MQTT seguro
MQTT_USR=                # Usuario del broker MQTT
MQTT_PASS=               # Contraseña del broker MQTT
ID_DISPOSITIVO=          # Topic base asociado al dispositivo