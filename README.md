# Bambu Studio Discord Rich Presence

Pequeño script en Python para mostrar un Rich Presence en Discord cuando `bambu-studio.exe` está corriendo.

## Requisitos

- Python 3.x
- `pypresence`

Instala la dependencia con:

```bash
pip install pypresence
```

## Configuración

Edita `config.ini` y completa tu `client_id` de la aplicación de Discord.

```ini
[discord]
client_id = TU_CLIENT_ID
large_image = bambu_studio
large_image_text = Bambu Studio
details = Slicing in Bambu Studio
state = 
poll_interval = 5
```

- `client_id`: Client ID de tu aplicación de Discord.
- `large_image`: clave del asset subido en Discord Developer Portal.
- `large_image_text`: texto que se ve al pasar el cursor sobre el ícono.
- `details`: texto principal del Rich Presence.
- `state`: texto secundario, opcional.
- `poll_interval`: intervalo de comprobación en segundos.

## Uso

Ejecuta el script desde la carpeta donde está `config.ini`:

```bash
pythonw bambu_presence.py
```

Si quieres compilarlo a `.exe` con PyInstaller:

```bash
pyinstaller --onefile --noconsole bambu_presence.py
```

Luego coloca `config.ini` en la misma carpeta del ejecutable.

## Comportamiento

- Si `bambu-studio.exe` está corriendo, activa el Rich Presence.
- Si se cierra, limpia el presence y sigue en espera.
- Cuando se vuelve a abrir, lo reactiva automáticamente.
# bambu-presence
# bambu-presence
