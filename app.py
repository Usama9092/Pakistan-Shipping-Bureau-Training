import psb_app.main as _app
import psb_app.private_video_streaming  # noqa: F401
from psb_app.professional_theme import apply_professional_theme
from psb_app.services.auto_publish_curriculum import prepare_and_publish_source_backed_curriculum


_base_style = _app.apply_style


def _professional_style() -> None:
    _base_style()
    apply_professional_theme()


_app.apply_style = _professional_style


if __name__ == "__main__":
    # Keep startup lightweight for every user session. Heavy assessment-bank
    # maintenance is executed separately from the login request path.
    _app.init_db()
    prepare_and_publish_source_backed_curriculum()
    _app.main()
