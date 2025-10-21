import asyncio, os, math, subprocess, tempfile
from pathlib import Path
from pyrogram import Client, errors
from config import MAX_UPLOAD_BYTES, THUMB_DIR, POST_UPLOAD_WAIT
import time

# ffprobe/ffmpeg helpers
def get_duration_seconds(file_path):
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode().strip()
        return int(float(out)) if out else 0
    except Exception:
        return 0

def make_thumbnail(file_path, thumb_path, time_pos=2):
    # create a thumbnail at 2 seconds (or nearest)
    cmd = [
        "ffmpeg",
        "-ss", str(time_pos),
        "-i", file_path,
        "-frames:v", "1",
        "-q:v", "2",
        "-y",
        str(thumb_path)
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

async def upload_file(client: Client, chat_id: int, file_entry: dict, progress_callback=None):
    """
    client: pyrogram Client
    chat_id: destination chat (int or '@channelusername')
    file_entry: { 'local_path': str, 'size': int, 'name': str }
    progress_callback: optional callable(bytes_sent, total_bytes) for progress
    """
    path = Path(file_entry["local_path"])
    size = path.stat().st_size
    if size >= MAX_UPLOAD_BYTES:
        # skip too big
        return False, "SKIPPED_TOO_BIG"

    duration = get_duration_seconds(str(path))
    # prepare thumbnail
    thumb_file = Path(THUMB_DIR) / (path.stem + ".jpg")
    make_thumbnail(str(path), str(thumb_file), time_pos=2)

    caption = f"{path.name}\nSize: {size} bytes\nDuration: {duration}s"

    tries = 0
    max_tries = 6
    while True:
        try:
            # send as video to be playable
            await client.send_video(
                chat_id,
                video=str(path),
                duration=duration if duration > 0 else None,
                thumb=str(thumb_file) if thumb_file.exists() else None,
                caption=caption,
                progress=progress_callback,
                supports_streaming=True,
                timeout=3600
            )
            # successful upload
            # wait POST_UPLOAD_WAIT seconds before next upload (auto trigger delay)
            await asyncio.sleep(POST_UPLOAD_WAIT)
            return True, "OK"
        except errors.FloodWait as fw:
            wait = fw.x + 2
            # log and sleep, exponential backoff limited
            await asyncio.sleep(wait)
            tries += 1
            if tries > max_tries:
                return False, f"FLOOD_MAX_RETRIES"
        except errors.RPCError as rpc:
            # handle spam/slowdown etc with backoff
            tries += 1
            if tries > max_tries:
                return False, f"RPC_{str(rpc)}"
            await asyncio.sleep(2 ** tries)
        except Exception as e:
            tries += 1
            if tries > max_tries:
                return False, f"ERR_{str(e)}"
            await asyncio.sleep(2 ** tries)
