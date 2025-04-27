import re, os, shutil, zipfile
from subprocess import Popen
import time
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from utils import *
from time import sleep
from datetime import datetime
from pySmartDL import SmartDL

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



print("PixelDrain bot Started!!!...")                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 ", flush=True)
app.run() 
