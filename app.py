import psb_app.main as _app
from psb_app.professional_theme import apply_professional_theme


_base_style = _app.apply_style


def _professional_style() -> None:
    _base_style()
    apply_professional_theme()


_app.apply_style = _professional_style


if __name__ == "__main__":
    _app.main()
