import re, asyncio, os, threading
from pyrogram import Client, filters
from config import API_ID, API_HASH, BOT_TOKEN, USE_USERBOT, SESSION_STRING
from downloader import download_mega_link
from uploader import upload_file
from indexer import add_files_for_link
from health_server import start_health_server

MEGA_LINK_RE = re.compile(r"(https?://mega\.nz/[^\s]+)")

app = Client(
    "mega_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN if not USE_USERBOT else None,
    session_string=SESSION_STRING if USE_USERBOT else None,
    workers=4
)

# A simple FIFO queue for jobs
job_queue = asyncio.Queue()


async def worker_loop(app):
    while True:
        job = await job_queue.get()
        chat_id = job["chat_id"]
        link = job["link"]
        msg = job["msg"]
        try:
            await app.send_message(chat_id, f"🔎 Processing MEGA link: {link}")
            files = download_mega_link(link)
            add_files_for_link(link, files)
            for f in files:
                size = f["size"]
                if size >= int(os.getenv("MAX_UPLOAD_BYTES", "2147483648")):
                    await app.send_message(chat_id, f"⛔ Skipped (>2GB): {f['name']}")
                    continue
                success, info = await upload_file(app, chat_id, f, progress_callback=None)
                if success:
                    await app.send_message(chat_id, f"✅ Uploaded: {f['name']}")
                else:
                    await app.send_message(chat_id, f"⚠️ Failed: {info}")
        except Exception as e:
            await app.send_message(chat_id, f"❌ Error processing {link}:\n{e}")
        finally:
            job_queue.task_done()


@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply_text("Send me a MEGA folder/file link, I’ll queue and upload playable files (skip >2GB).")


@app.on_message(filters.text)
async def handle_text(client, message):
    m = MEGA_LINK_RE.search(message.text or "")
    if not m:
        return
    link = m.group(1)
    status_msg = await message.reply_text(f"Queued: {link}")
    await job_queue.put({"chat_id": message.chat.id, "link": link, "msg": status_msg})

def start_q(bot):
    def run_asyncio():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(worker_loop(bot))

    thread = threading.Thread(target=run_asyncio)
    thread.daemon = True  # Set the thread as a daemon thread
    thread.start()

start_health_server()
start_q(app)
if __name__ == "__main__":
    bot.run()
