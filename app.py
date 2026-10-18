import os
import shutil
import tempfile
from urllib.parse import urlparse

import streamlit as st
import yt_dlp

st.set_page_config(page_title="Video Fetch", layout="centered")

# Only these sites are accepted.
ALLOWED_SITES = (
    "tiktok.com",
    "youtube.com",
    "youtu.be",
    "facebook.com",
    "fb.watch",
    "instagram.com",
)

# Free servers have limited memory, so keep downloads small (in bytes).
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


def is_allowed(url):
    """Return True if the link is from one of the supported sites."""
    host = (urlparse(url).hostname or "").lower()
    return any(host == site or host.endswith("." + site) for site in ALLOWED_SITES)


def fetch_video(url):
    """Download the video and return (file_name, file_bytes)."""
    temp_dir = tempfile.mkdtemp()
    options = {
        "outtmpl": os.path.join(temp_dir, "%(title).60s.%(ext)s"),
        # Picks one ready-made mp4 file, so ffmpeg isn't required.
        "format": "best[ext=mp4]/best",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "max_filesize": MAX_FILE_SIZE,
    }
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        with open(file_path, "rb") as f:
            data = f.read()
        return os.path.basename(file_path), data
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


st.title("Video Fetch")
st.write("Paste a public video link and save the video to your device.")

url = st.text_input("Video link", placeholder="https://www.tiktok.com/@user/video/...")

if st.button("Download video", type="primary", use_container_width=True):
    st.session_state.pop("video", None)
    link = url.strip()

    if not link.startswith(("http://", "https://")):
        st.error("Paste a full link that starts with https://")
    elif not is_allowed(link):
        st.error("This site isn't supported. Use TikTok, YouTube, Facebook or Instagram.")
    else:
        try:
            with st.spinner("Downloading… this can take up to a minute."):
                name, data = fetch_video(link)
            st.session_state["video"] = (name, data)
        except Exception:
            st.error("Couldn't download this video. Check that the link is public and try again.")

# Show the save button once a video is ready.
if "video" in st.session_state:
    name, data = st.session_state["video"]
    st.success("Your video is ready.")
    st.download_button(
        "Save video",
        data=data,
        file_name=name,
        mime="video/mp4",
        use_container_width=True,
    )

st.caption("Works with TikTok, YouTube, Facebook and Instagram.")
st.caption("Only download videos you own or have permission to save. Private videos can’t be downloaded.")
