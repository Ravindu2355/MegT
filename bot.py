import re, asyncio, os, time
from pyrogram import Client, filters
from config import API_ID, API_HASH, BOT_TOKEN, USE_USERBOT, SESSION_STRING, WORK_DIR
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
processing = False

async def worker_loop():
    global processing
    processing = True
    while True:
        job = await job_queue.get()
        chat_id = job["chat_id"]
        link = job["link"]
        msg = job["msg"]
        try:
            await app.send_message(chat_id, f"🔎 Processing MEGA link: {link}")
            files = download_mega_link(link)  # synchronous; may be long
            # record metadata
            add_files_for_link(link, files)
            # upload files sequentially
            for f in files:
                # skip if > limit
                size = f["size"]
                if size >= int(os.getenv("MAX_UPLOAD_BYTES", "2147483648")):
                    await app.send_message(chat_id, f"⛔ Skipped (>{os.getenv('MAX_UPLOAD_BYTES')}) : {f['name']}")
                    continue
                # progress callback
                async def progress(current, total):
                    # update existing message or send small updates
                    try:
                        await app.edit_message_text(chat_id, msg.message_id, f"Uploading {f['name']} — {current}/{total}")
                    except Exception:
                        pass

                success, info = await upload_file(app, chat_id, f, progress_callback=None)
                if success:
                    await app.send_message(chat_id, f"✅ Uploaded: {f['name']}")
                else:
                    await app.send_message(chat_id, f"⚠️ Failed/Skipped {f['name']}: {info}")

        except Exception as e:
            await app.send_message(chat_id, f"❌ Error processing link {link}:\n{e}")
        finally:
            job_queue.task_done()

@Client.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply_text("Send me a MEGA folder/file link and I'll enqueue and upload the playable videos (skip >2GB).")

@Client.on_message(filters.text)
async def handle_text(client, message):
    txt = message.text or ""
    m = MEGA_LINK_RE.search(txt)
    if not m:
        return
    link = m.group(1)
    # enqueue job
    status_msg = await message.reply_text(f"Queued: {link}")
    await job_queue.put({"chat_id": message.chat.id, "link": link, "msg": status_msg})

async def start_bot():
    # start health server
    asyncio.create_task(start_health_server())
    # start worker loop
    asyncio.create_task(worker_loop()
    print("Bot started")
    await app.run()
    # keep running
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(start_bot())
