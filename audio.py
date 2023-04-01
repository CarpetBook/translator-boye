import ffmpeg
import requests
import time

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
