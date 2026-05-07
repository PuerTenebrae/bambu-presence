# BambuPresence

Muestra el estado de Bambu Studio en tu perfil de Discord en tiempo real.
Detecta automáticamente cuando la aplicación está abierta o cerrada y actualiza el presence en consecuencia.

## Instalación

1. Descargá el `.rar` desde [Releases](../../releases)
2. Extraé la carpeta
3. Ejecutá `bambu_presence.exe`

No requiere Python ni dependencias adicionales.

## Configuración

El `config.ini` incluido ya viene configurado y listo para usar. Si querés personalizar el texto que se muestra en Discord, podés editarlo:

| Campo | Descripción |
|---|---|
| `details` | Texto principal del Rich Presence |
| `state` | Texto secundario, opcional |
| `poll_interval` | Intervalo de comprobación en segundos |
| `autostart` | Inicia automáticamente con Windows (`true` / `false`) |

Por defecto todos los valores están configurados y el autostart desactivado. Cambiá `autostart = true` para que el programa arranque solo con Windows.

## Comportamiento

- Si `bambu-studio.exe` está corriendo, activa el Rich Presence
- Si se cierra, limpia el presence y sigue en espera
- Cuando se vuelve a abrir, lo reactiva automáticamente

## Para desarrolladores

El código fuente completo está disponible en este repositorio.
Requiere Python 3.x y `pypresence`:

```bash
pip install pypresence
```