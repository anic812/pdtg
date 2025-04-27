import requests
import math
import time
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
