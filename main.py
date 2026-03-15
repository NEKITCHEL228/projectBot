import os
import threading

from aiohttp.web import run_app

from app.backend.web.app import setup_app

#Остановка бота при помощи Ctrl + C
def _suppress_keyboard_interrupt(args):
    if args.exc_type is KeyboardInterrupt:
        return
    threading.__excepthook__(args)

threading.excepthook = _suppress_keyboard_interrupt


if __name__ == "__main__":
    run_app(
        setup_app(
            config_path=os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "config.yml"
            )
        )
    )