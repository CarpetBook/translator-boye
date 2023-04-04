import discord
import whisper
import zipfile
import langcodes
from whisper.utils import get_writer

model = None
trans_exts = ["txt", "vtt", "srt", "tsv", "json"]


async def transcriber(respond: discord.Message, file, task="transcribe"):
    global model
    wait = None
    if model is None:
        wait = await respond.channel.send("Loading model...")
        model = whisper.load_model("large-v2")
        await wait.delete()
    editmsg = await respond.channel.send(content="Transcribing...")
    result = model.transcribe(file, verbose=True, task=task, compression_ratio_threshold=1.5, decode_options={"beam_size": 2})

    # file writer
    writer = get_writer("all", "transcripts")

    # it doesn't really matter if this is technically wrong,
    # it just needs to be unique
    filename = file.split("\\")[-1].split(".")[0]

    # write transcripts
    writer(result, f"transcripts\\{filename}")

    # zip transcripts
    with zipfile.ZipFile(f"transcripts\\{filename}.zip", "w") as zip:
        for ext in trans_exts:
            zip.write(f"transcripts\\{filename}.{ext}", arcname=f"{filename}.{ext}")

    # print the recognized text
    print(result)

    # result[text] doesn't have newlines
    # use the segments and split by \n
    newtext = ""
    for segment in result["segments"]:
        stamp = maketimestamp(segment["start"], segment["end"])
        newtext += stamp + " " + segment["text"] + "\n"

    # get the language name from the language code, cheap way of detecting language
    source_lang = langcodes.Language(result["language"]).language_name()

    response = f"Transcribed. Source language: {source_lang} \n```{newtext}```"
    if len(newtext) > 1900:
        response = f"Transcribed. Source language: {source_lang}\n```{newtext[:1900] + '...'}```"

    zippy = discord.File(f"transcripts\\{filename}.zip")

    await respond.reply(response, file=zippy)
    await editmsg.delete()


def maketimestamp(startsec, endsec):
    starthr = startsec // 3600
    startmin = startsec // 60
    startsec = startsec % 60
    endhr = endsec // 3600
    endmin = endsec // 60
    endsec = endsec % 60
    print(starthr, startmin, startsec, endhr, endmin, endsec)
    starthr = "{:02d}".format(int(starthr))
    startmin = "{:02d}".format(int(startmin))
    if startsec < 10:
        startsec = "0" + "{:05.3f}".format(float(startsec))
    else:
        startsec = "{:05.3f}".format(float(startsec))

    endhr = "{:02d}".format(int(endhr))
    endmin = "{:02d}".format(int(endmin))
    if endsec < 10:
        endsec = "0" + "{:05.3f}".format(float(endsec))
    else:
        endsec = "{:05.3f}".format(float(endsec))
    return f"[{starthr}:{startmin}:{startsec} -> {endhr}:{endmin}:{endsec}]"
