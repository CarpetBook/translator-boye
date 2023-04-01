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
    editmsg = await wait.edit("Transcribing...")
    result = model.transcribe(file, verbose=True, task=task, temperature=0)

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
        newtext += segment["text"] + "\n"

    # get the language name from the language code, cheap way of detecting language
    source_lang = langcodes.Language(result["language"]).language_name()

    response = f"Transcribed. Source language: {source_lang} \n```{newtext}```"
    if len(newtext) > 1900:
        response = f"Transcribed. Source language: {source_lang}\n```{newtext[:1900] + '...'}```"

    zippy = discord.File(f"transcripts\\{filename}.zip")
    
    await respond.reply(response, file=zippy)
    await editmsg.delete()
