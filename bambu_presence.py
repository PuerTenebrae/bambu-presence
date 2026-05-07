import configparser
import logging
import os
import subprocess
import sys
import time
import winreg

from pypresence import Presence

CONFIG_FILENAME  = "config.ini"
AUTOSTART_KEY    = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_NAME   = "BambuPresence"
DEFAULTS = {
    "client_id":        "1501971486267936841",
    "large_image":      "https://i.imgur.com/mecfhUi.png",  # reemplazá con tu URL
    "large_image_text": "Bambu Studio",
    "details":          "Slicing in Bambu Studio",
    "state":            "Working on a print",
    "poll_interval":    5,
    "autostart":        False,
}
PROCESS_NAME = "bambu-studio.exe"


# ── Logging ───────────────────────────────────────────────────────────────────

def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    ))
    logging.basicConfig(level=logging.DEBUG, handlers=[handler])


log = logging.getLogger("bambu_presence")


# ── Config ────────────────────────────────────────────────────────────────────

def get_base_path():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def load_config(config_path):
    log.debug(f"Cargando config desde: {config_path}")

    if not os.path.exists(config_path):
        log.warning("config.ini no encontrado — usando valores por defecto")
        return DEFAULTS.copy()

    config = configparser.ConfigParser()
    try:
        config.read(config_path, encoding="utf-8")
    except Exception as e:
        log.error(f"Error leyendo config.ini: {e} — usando valores por defecto")
        return DEFAULTS.copy()

    section = config["discord"] if "discord" in config else {}
    values = {
        "client_id":        section.get("client_id",        DEFAULTS["client_id"]).strip(),
        "large_image":      section.get("large_image",      DEFAULTS["large_image"]).strip(),
        "large_image_text": section.get("large_image_text", DEFAULTS["large_image_text"]).strip(),
        "details":          section.get("details",          DEFAULTS["details"]).strip(),
        "state":            section.get("state",            DEFAULTS["state"]).strip(),
        "poll_interval":    DEFAULTS["poll_interval"],
        "autostart":        DEFAULTS["autostart"],
    }

    try:
        values["poll_interval"] = max(1, int(section.get("poll_interval", DEFAULTS["poll_interval"])))
    except Exception:
        log.warning("poll_interval invalido en config.ini — usando 5s por defecto")

    try:
        values["autostart"] = section.getboolean("autostart", DEFAULTS["autostart"])
    except Exception:
        log.warning("autostart invalido en config.ini — usando false por defecto")

    log.info(f"Config cargada  |  client_id={values['client_id'] or '(vacío)'}  "
             f"poll={values['poll_interval']}s  autostart={values['autostart']}  "
             f"details='{values['details']}'  state='{values['state']}'")

    if not values["client_id"]:
        log.error("client_id está vacío en config.ini — Rich Presence no va a funcionar")

    return values


# ── Autostart ─────────────────────────────────────────────────────────────────

def configurar_autostart(activar):
    """Agrega o elimina la entrada de autostart en el registro de Windows."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            AUTOSTART_KEY,
            0,
            winreg.KEY_SET_VALUE,
        )
        if activar:
            exe_path = sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__)
            winreg.SetValueEx(key, AUTOSTART_NAME, 0, winreg.REG_SZ, f'"{exe_path}"')
            log.info(f"Autostart activado: {exe_path}")
        else:
            try:
                winreg.DeleteValue(key, AUTOSTART_NAME)
                log.info("Autostart desactivado")
            except FileNotFoundError:
                pass  # ya no estaba, no pasa nada
        winreg.CloseKey(key)
    except Exception as e:
        log.warning(f"No se pudo configurar autostart: {e}")


# ── Proceso ───────────────────────────────────────────────────────────────────

def is_bambu_running():
    try:
        output = subprocess.check_output(
            ["tasklist", "/FI", f"IMAGENAME eq {PROCESS_NAME}"],
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        normalized = output.lower()
        if "no tasks are running" in normalized:
            return False
        return PROCESS_NAME in normalized
    except Exception as e:
        log.warning(f"Error chequeando proceso: {e}")
        return False


# ── Rich Presence ─────────────────────────────────────────────────────────────

class DiscordPresence:
    def __init__(self, client_id, details, state, large_image, large_image_text):
        self.client_id        = client_id
        self.details          = details
        self.state            = state
        self.large_image      = large_image
        self.large_image_text = large_image_text
        self.rpc              = None
        self.connected        = False

    def connect(self):
        if self.connected:
            return True

        if not self.client_id:
            log.error("No hay client_id configurado — no se puede conectar a Discord")
            return False

        log.info(f"Conectando a Discord  (client_id={self.client_id})...")
        try:
            self.rpc = Presence(self.client_id)
            self.rpc.connect()
            self.connected = True
            log.info("Conexión con Discord establecida")
            return True
        except Exception as e:
            log.error(f"No se pudo conectar a Discord: {e}")
            log.debug("¿Discord Desktop está abierto?")
            self.connected = False
            self.rpc = None
            return False

    def update(self, start_timestamp):
        if not self.connect():
            return False

        try:
            self.rpc.update(
                details=self.details,
                state=self.state,
                large_image=self.large_image,
                large_text=self.large_image_text,
                start=start_timestamp,
            )
            log.info(f"Presence actualizada  |  details='{self.details}'  state='{self.state}'")
            return True
        except Exception as e:
            log.error(f"Error actualizando presence: {e}")
            self.disconnect()
            return False

    def clear(self):
        if not self.connected or not self.rpc:
            return

        log.info("Limpiando presence (Bambu cerrado)")
        try:
            self.rpc.clear()
        except Exception as e:
            log.warning(f"Error limpiando presence: {e}")
        finally:
            self.disconnect()

    def disconnect(self):
        if self.rpc:
            try:
                self.rpc.close()
            except Exception:
                pass
        self.rpc = None
        self.connected = False
        log.debug("Desconectado de Discord")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    setup_logging()
    log.info("=== Bambu Studio Discord Presence iniciando ===")

    base_path   = get_base_path()
    config_path = os.path.join(base_path, CONFIG_FILENAME)
    config      = load_config(config_path)

    configurar_autostart(config["autostart"])

    presence = DiscordPresence(
        client_id=config["client_id"],
        details=config["details"],
        state=config["state"],
        large_image=config["large_image"],
        large_image_text=config["large_image_text"],
    )

    log.info(f"Monitoreando proceso: {PROCESS_NAME}  (cada {config['poll_interval']}s)")

    process_was_running     = False
    current_start_timestamp = None

    while True:
        is_running = is_bambu_running()

        if is_running:
            if current_start_timestamp is None:
                current_start_timestamp = int(time.time())

            if not process_was_running:
                log.info("Bambu Studio detectado — activando presence")
                ok = presence.update(start_timestamp=current_start_timestamp)
                if not ok:
                    log.warning("Presence no se pudo activar — se va a reintentar en el próximo ciclo")
                process_was_running = True

            elif not presence.connected:
                log.debug("Presence desconectada — reintentando reconexión")
                presence.update(start_timestamp=current_start_timestamp)

        if not is_running and process_was_running:
            log.info("Bambu Studio cerrado — desactivando presence")
            presence.clear()
            process_was_running     = False
            current_start_timestamp = None

        time.sleep(config["poll_interval"])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("Detenido por el usuario (Ctrl+C)")
        sys.exit(0)
