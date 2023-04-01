import ffmpeg
import requests
import time
import yt_dlp

sr = 16000


def downloadAudio(url, ext):
    try:
        r = requests.get(url)
        # download file
        name = f"audios\\{time.time()}.{ext}"
        with open(name, "wb") as f:
            f.write(r.content)
        return ("success", name)
    except requests.exceptions.RequestException as e:
        print(f"Something about a provided audio file was malformed, or the request failed. {e}")
        return ("fail", e)


def convertAudio(filename):
    try:
        out, _ = (
            ffmpeg.input(filename, threads=0)
            .output("-", format="s16le", acodec="pcm_s16le", ac=1, ar=sr)
            .run(cmd=["ffmpeg", "-nostdin"], capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        raise RuntimeError(f"Failed to load audio: {e.stderr.decode()}") from e


def downloadYoutubeAudio(link):
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
        'postprocessors': [{  # Extract audio using ffmpeg
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
        }],
        'paths': {
            'home': './audios',
        },
        'outtmpl': '%(id)s.%(ext)s',
    }

    info = None
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=False)
        ydl.download(link)

    # print(info)
    return ("success", "audios\\" + info["id"] + ".m4a")
