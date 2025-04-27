import re, os, shutil
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from time import sleep
from datetime import datetime
from pySmartDL import SmartDL
import requests
import math
from random import choice
APP_ID = "23028247"
API_HASH = "659c5f1124a81ad789a6ea021da73f4d"
BOT_TOKEN = "7559848398:AAHz9r5S0PF1ab8TxYtr9ijYaf1v6IBIJdQ"


def progress_bar(current, total, ud_type, message, start):
    now = time.time()
    diff = now - start
    if round(diff % 5.00) == 0 or current == total:
        # if round(current / total * 100, 0) % 5 == 0:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time = TimeFormatter(milliseconds=elapsed_time)
        estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)

        progress = "[{0}{1}] | {2}%\n".format(
            "".join(["■" for i in range(math.floor(percentage / 10))]),
            "".join(["□" for i in range(10 - math.floor(percentage / 10))]),
            round(percentage, 2),
        )

        tmp = progress + "{0} of {1}\n**Speed**: {2}/s\n**ETA**: {3}\n".format(
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            # elapsed_time if elapsed_time != '' else "0 s",
            estimated_total_time if estimated_total_time != "" else "0 s",
        )
        try:
            message.edit(text="Uploading -> **{}**\n {}".format(ud_type, tmp))
            time.sleep(4)
        except:
            pass


def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        ((str(days) + "d, ") if days else "")
        + ((str(hours) + "h, ") if hours else "")
        + ((str(minutes) + "m, ") if minutes else "")
        + ((str(seconds) + "s, ") if seconds else "")
        + ((str(milliseconds) + "ms, ") if milliseconds else "")
    )
    return tmp[:-2]


def humanbytes(size):
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: " ", 1: "K", 2: "M", 3: "G", 4: "T"}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + "B"


def file_info(file_id):
    worker = choice(WORKERS)
    file = requests.get(f"https://{worker}/api/file/{file_id}/info").json()
    #file = requests.get(f"https://pixeldrain.com/api/file/{file_id}/info").json()
    return {"title": file["name"], "id": file["id"], "size": humanbytes(file["size"])}


def file_dl(file_id):
    """Return direct download URL using worker servers"""
    return get_worker_url(file_id)

LINK_REGEX = r"^https:\/\/pixeldrain\.com\/[lu]\/([a-zA-Z0-9]+)(#item=\d+)?$"

WORKERS = [
    "pd1.sriflix.online",
    "pd2.sriflix.online", 
    "pd3.sriflix.online",
    "pd4.sriflix.online",
    "pd5.sriflix.online"
]

def get_worker_url(file_id):
    worker = choice(WORKERS)
    return f"https://{worker}/api/file/{file_id}?download"

def list_info(list_id):
    worker = choice(WORKERS)
    data = requests.get(f"https://{worker}/api/list/{list_id}").json()
    return {
        "file_count": data["file_count"],
        "title": data["title"],
        "files": [
            {"title": file["name"], "id": file["id"], "size": humanbytes(file["size"])}
            for file in data["files"]
        ],
    }
app = Client("pd-dl_bot", api_id=APP_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
c_time = None


@app.on_message(filters.command("start"))
def start_command(client: Client, message):
    client.send_message(
        message.chat.id,
        text=f"Hello {message.from_user.first_name},\n I'm a PixelDrain Downloder Bot! Send me a URL with /l/ to download all files in a list or /u/ for individual files.",
    )

# Function to download a single file using worker API
def download_single_file(file_id, download_dir, progress_msg, chat_id=None, message_id=None):
    worker_url = get_worker_url(file_id)
    file_data = file_info(file_id)
    custom_file_name = file_data["title"]
    download_file_path = os.path.join(download_dir, custom_file_name)
    
    worker_name = worker_url.split("//")[1].split("/")[0].split(".")[0]
    
    if progress_msg:
        app.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"Downloading **'{custom_file_name}'** via {worker_name}\nPlease wait...",
        )
    
    downloader = SmartDL(worker_url, download_file_path, progress_bar=False)
    downloader.start(blocking=False)
    c_time = time.time()
    
    while not downloader.isFinished():
        total_length = downloader.filesize if downloader.filesize else None
        downloaded = downloader.get_dl_size()
        display_message = ""
        now = time.time()
        diff = now - c_time
        percentage = downloader.get_progress() * 100
        speed = downloader.get_speed()
        progress_str = "[{0}{1}]\nProgress: {2}%".format(
            "".join(["█" for i in range(math.floor(percentage / 5))]),
            "".join(["░" for i in range(20 - math.floor(percentage / 5))]),
            round(percentage, 2),
        )
        estimated_total_time = downloader.get_eta(human=True)
        
        if progress_msg and chat_id and message_id:
            try:
                current_message = f"{progress_msg} ⏬ via {worker_name}\n"
                current_message += f"{progress_str}\n"
                current_message += f"{humanbytes(downloaded)} of {humanbytes(total_length)}\n"
                current_message += f"**ETA:** {estimated_total_time}\n"
                current_message += f"**Speed:** {humanbytes(speed)}/s "
                
                if round(diff % 8.00) == 0 and current_message != display_message:
                    app.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=current_message,
                    )
                    display_message = current_message
                    sleep(2)
            except Exception:
                pass  # Ignore message editing errors
    
    # Return the path if file was downloaded successfully
    if os.path.exists(download_file_path):
        return download_file_path
    return None

@app.on_message((filters.text & filters.private))
def main_processer(client, message):
    download_dir = ""
    try:
        msg = app.send_message(message.chat.id, "Processing")
        url = message.text.strip()
        match = re.match(LINK_REGEX, url)
        if match:
            chat_id = message.chat.id
            message_id = msg.id
            pd_id = match.group(1)
            app.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="Analysing link...\nPlease Wait.",
            )
            download_dir = f"downloads/{chat_id}_{message_id}"

            if not os.path.exists(download_dir):
                os.makedirs(download_dir)
                
            if "/l/" in url:
                # This is a list URL - get all file IDs and download them
                list_data = list_info(pd_id)
                
                # First, send list info
                list_title = list_data["title"]
                file_count = list_data["file_count"]
                
                app.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=f"**List Title:** {list_title}\n**Number of Files:** {file_count}\n\nStarting download of all files...",
                )
                
                # Download each file in the list
                downloaded_files = []
                for index, file in enumerate(list_data["files"]):
                    file_id = file["id"]
                    file_title = file["title"]
                    
                    app.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=f"Downloading file {index+1}/{file_count}\n**{file_title}**",
                    )
                    
                    # Download the file
                    file_path = download_single_file(
                        file_id, 
                        download_dir, 
                        progress_msg=f"Downloading file {index+1}/{file_count}\n ⏬**{file_title}**", 
                        chat_id=chat_id, 
                        message_id=message_id
                    )
                    
                    if file_path:
                        downloaded_files.append(file_path)
                        app.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            text=f"Downloaded {index+1}/{file_count}: {file_title}",
                        )
                    
                # After all files are downloaded
                app.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=f"Downloaded {len(downloaded_files)}/{file_count} files from list '{list_title}'.\nPreparing to send...",
                )
                
            else:
                # Single file download
                start_t = datetime.now()
                
                # Download the file using our download function
                file_path = download_single_file(
                    pd_id, 
                    download_dir, 
                    progress_msg=True, 
                    chat_id=chat_id, 
                    message_id=message_id
                )
                
                end_t = datetime.now()
                ms = (end_t - start_t).seconds
                
                if file_path:
                    app.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=f"Downloaded in {ms} seconds. Preparing to send...",
                    )

            # Now gather all files to send
            app.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="Preparing files to send...",
            )
            
            files_up = []
            for root, dirs, files in os.walk(download_dir):
                for file in files:
                    if (
                        file.endswith(".flac")
                        or file.endswith(".m4a")
                        or file.endswith(".png")
                        or file.endswith(".jpg")
                        or file.endswith(".jpeg")
                        or file.endswith(".lrc")
                        or file.endswith(".mp4")
                        or file.endswith(".mkv")
                        or file.endswith(".mp3")
                        or file.endswith(".pdf")
                        or file.endswith(".zip")
                        or file.endswith(".rar")
                        or file.endswith(".txt")
                    ):
                        filepath = os.path.join(root, file)
                        files_up.append(filepath)

            if not files_up:
                app.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text="No compatible files found to send. Please try again or contact admin.",
                )
                shutil.rmtree(download_dir)
                return
                
            # Send all files
            if files_up:
                c_time = time.time()
                
                # Update message to show upload starting
                app.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=f"Uploading {len(files_up)} files...",
                )
                
                for index, file in enumerate(files_up):
                    fileN = os.path.basename(file)
                    try:
                        app.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            text=f"Uploading file {index+1}/{len(files_up)}: {fileN}",
                        )
                        
                        app.send_document(
                            chat_id=chat_id,
                            document=file,
                            progress=progress_bar,
                            progress_args=(fileN, msg, c_time),
                        )
                        time.sleep(1)
                    except FloodWait as e:
                        time.sleep(e.value)
                        app.send_document(
                            chat_id=chat_id,
                            document=file,
                            progress=progress_bar,
                            progress_args=(fileN, msg, c_time),
                        )
                        time.sleep(1)
                    except Exception as e:
                        app.send_message(
                            chat_id=chat_id,
                            text=f"Error uploading {fileN}: {str(e)}",
                        )
                
            # Clean up
            shutil.rmtree(download_dir)
            print("Sent successfully, Files sent and folder removed.", flush=True)
            app.delete_messages(chat_id=chat_id, message_ids=message_id)
            app.send_message(
                chat_id=chat_id,
                reply_to_message_id=message.id,
                text="**Download and upload completed!**",
            )
            #print("Completed", flush=True)
        else:
            app.send_message(
                chat_id=message.chat.id, text="Invalid ```PixelDrain``` link. Format should be https://pixeldrain.com/u/ID or https://pixeldrain.com/l/ID"
            )
    except Exception as e:
        app.send_message(
            chat_id=message.chat.id, text=f"Something went wrong:\n{e}"
        )
        if download_dir:
            if os.path.exists(download_dir):
                shutil.rmtree(download_dir)


print("Bot Started")
app.run()
