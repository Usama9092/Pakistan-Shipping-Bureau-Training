import psb_app.main as _app
import psb_app.private_video_streaming  # noqa: F401
from psb_app.professional_theme import apply_professional_theme
from psb_app.services.auto_publish_curriculum import prepare_and_publish_source_backed_curriculum
from psb_app.services.professional_assessment_bank import ensure_professional_assessment_banks


_base_style = _app.apply_style


def _professional_style() -> None:
    _base_style()
    apply_professional_theme()


_app.apply_style = _professional_style


if __name__ == "__main__":
    # Ensure the persistent schema is ready before controlled curriculum maintenance.
    _app.init_db()
    prepare_and_publish_source_backed_curriculum()
    ensure_professional_assessment_banks()
    _app.main()
