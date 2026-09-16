"""Private, low-overhead training video streaming.

Videos stay in the private Supabase Storage bucket. Learners receive only a
short-lived signed URL and the browser streams the media directly from storage;
the Streamlit app never downloads the whole video into server memory.
"""
from __future__ import annotations

from html import escape

from psb_app.common import actor_get, clean, db_where, pd, secure_file_url, st, table_exists
from psb_app.services import training_certification as tc
from psb_app.pages import training as training_page


_ORIGINAL_TRAINEE_TRAINING = training_page.trainee_training


def _private_video_resources(training_id: str) -> pd.DataFrame:
    if not table_exists("training_resources"):
        return pd.DataFrame()
    rows = db_where(
        "training_resources",
        "training_id = :tid AND active = :active",
        (("tid", training_id), ("active", "Yes")),
    )
    if rows.empty:
        return rows
    return rows[rows.get("resource_type", pd.Series(dtype=str)).astype(str).eq("Private Stream Video")]


def _video_file(resource: dict) -> dict:
    ref = clean(resource.get("rule_reference"))
    if not ref.startswith("FILE:"):
        return {}
    file_id = ref.split(":", 1)[1].strip()
    rows = db_where("files", "file_id = :fid", (("fid", file_id),))
    return rows.iloc[-1].to_dict() if not rows.empty else {}


def _render_video(url: str, title: str) -> None:
    safe_url = escape(url, quote=True)
    safe_title = escape(title)
    html = f"""
    <div style="font-family:Arial,sans-serif;margin:0 0 10px 0;">
      <div style="font-weight:700;margin-bottom:8px;color:#0b1f33;">{safe_title}</div>
      <video controls controlsList="nodownload noremoteplayback" disablePictureInPicture
             preload="metadata" oncontextmenu="return false;"
             style="width:100%;max-height:520px;background:#000;border-radius:12px;"
             src="{safe_url}"></video>
      <div style="font-size:12px;color:#5b6775;margin-top:6px;">
        Private training stream · temporary signed access · direct from secure storage
      </div>
    </div>
    """
    st.components.v1.html(html, height=430, scrolling=False)


def _render_external_video(url: str) -> None:
    value = clean(url)
    lower = value.lower()
    if not value:
        return
    if "youtube.com/" in lower or "youtu.be/" in lower or "vimeo.com/" in lower or lower.endswith(".mp4"):
        st.markdown("### Training Video")
        st.caption("Streamed by the external video provider; it does not consume Render application memory or bandwidth.")
        st.video(value)


def trainee_training_with_private_stream(actor, training_id: str) -> None:
    user_id = clean(actor_get(actor, "user_id", ""))
    tr = tc._training(training_id)
    rec = tc._record(user_id, training_id) if user_id else {}
    sequence_ok, _ = tc._sequence_gate(user_id, training_id) if user_id else (False, [])

    if tr and rec and sequence_ok and clean(tr.get("content_status")) == "Published":
        _render_external_video(clean(tr.get("video_link")))
        videos = _private_video_resources(training_id)
        if not videos.empty:
            st.markdown("### Private Streaming Video")
            st.caption("Video is streamed from private object storage so it does not consume Render application memory or application bandwidth.")
            videos = videos.sort_values("sequence_no") if "sequence_no" in videos.columns else videos
            for _, resource in videos.iterrows():
                resource_dict = resource.to_dict()
                rid = clean(resource_dict.get("resource_id"))
                file_row = _video_file(resource_dict)
                title = clean(resource_dict.get("title")) or clean(file_row.get("file_name")) or "Training Video"
                if not file_row:
                    st.warning(f"Private video source is not available: {title}")
                    continue
                signed_url = secure_file_url(file_row)
                if not signed_url:
                    st.warning(f"Unable to create secure streaming access for: {title}")
                    continue
                _render_video(signed_url, title)
                if tc._progress_done(user_id, training_id, "Resource", rid):
                    st.success("Video viewing acknowledgement recorded.")
                elif st.button("I have viewed this training video", key=f"private_video_done_{training_id}_{rid}"):
                    tc._mark_progress(user_id, training_id, "Resource", rid)
                    tc.sync_training_record(user_id, training_id)
                    st.rerun()

    _ORIGINAL_TRAINEE_TRAINING(actor, training_id)


def install_private_video_streaming() -> None:
    training_page.trainee_training = trainee_training_with_private_stream
    tc.enhanced_trainee_training = trainee_training_with_private_stream


install_private_video_streaming()
