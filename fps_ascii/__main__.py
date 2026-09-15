"""Permite executar: python -m fps_ascii."""
import os
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")


def main():
    try:
        from .app import main as run
    except ModuleNotFoundError as exc:
        if exc.name != "pygame":
            raise
        print("FPS ASCII precisa de pygame-ce.")
        print("Instale com: python -m pip install -r requirements.txt")
        return 1
    return run()


if __name__ == "__main__":
    raise SystemExit(main())

