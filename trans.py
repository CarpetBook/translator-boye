import discord
import whisper
import zipfile
import langcodes
from whisper.utils import get_writer

model = whisper.load_model("large-v2")
trans_exts = ["txt", "vtt", "srt", "tsv", "json"]


async def transcriber(respond: discord.Message, file, task="transcribe"):
    editmsg = await respond.channel.send("Transcribing...")
    result = model.transcribe(file, verbose=True, task=task, temperature=0)

    writer = get_writer("all", "transcripts")

    filename = file.split("\\")[-1].split(".")[0]

    writer(result, f"transcripts\\{filename}")

    # zip transcripts
    with zipfile.ZipFile(f"transcripts\\{filename}.zip", "w") as zip:
        for ext in trans_exts:
            zip.write(f"transcripts\\{filename}.{ext}", arcname=f"{filename}.{ext}")

    # print the recognized text
    print(result)
    newtext = ""
    for segment in result["segments"]:
        newtext += segment["text"] + "\n"

    source_lang = langcodes.Language(result["language"]).language_name()
    response = f"Transcribed. Source language: {source_lang} \n```{newtext}```"
    if len(newtext) > 1900:
        response = f"Transcribed.\n```{newtext[:1900] + '...'}```"

    zippy = discord.File(f"transcripts\\{filename}.zip")
    await respond.reply(response, file=zippy)
    await editmsg.delete()
