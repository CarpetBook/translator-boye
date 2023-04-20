import discord
from discord import app_commands
import openai
import json
import tenacity
import tiktoken
# generators
from generators import text
from generators import audio
from generators import images
from generators import summarizer
from generators import trans

# experimental features and tools
from tools.memory import ChatMemory
from tools import ocr
from tools import resnet
from tools import moderation
from tools import vectors

import asyncio
import re

import random
import string

from csv_logger import CsvLogger
import logging

filename = 'logs/translator_boye_tokens.csv'
delimiter = ','
level = logging.INFO
custom_additional_levels = ['tokens']
fmt = f'%(asctime)s{delimiter}%(levelname)s{delimiter}%(message)s'
datefmt = '%Y/%m/%d %H:%M:%S'
# max_size = 1024  # 1 kilobyte
max_files = 100000
header = ['date', 'prompt', 'generated', 'total']

# Creat logger with csv rotating handler
csvlogger = CsvLogger(filename=filename,
                      delimiter=delimiter,
                      level=level,
                      add_level_names=custom_additional_levels,
                      add_level_nums=None,
                      fmt=fmt,
                      datefmt=datefmt,
                      #   max_size=max_size,
                      max_files=max_files,
                      header=header)

TEXT_EXT = ["txt", "md", "py", "js", "cpp", "c", "json", "yaml", "yml"]
IMG_EXT = ["png", "jpg", "jpeg", "webp", "bmp", "tiff", "tif", "jfif", "exif"]
URL_REGEX = r"(?:\s|^)(https?:\/\/[^\s]+)"

chat_channel_ids = []
server_options = {}

internal_password = None

# define the length of your random string
length = 10

# create a list of all possible characters for your string
characters = string.ascii_letters + string.digits + '!@#$%^&*()'

# use the random.sample() function to generate a list of 'length' number of random characters from the 'characters' list
internal_password = ''.join(random.sample(characters, length))

print(f"Password: {internal_password}")

tik = tiktoken.get_encoding("cl100k_base")

with open("keys.json") as filey:
    wee = json.load(filey)
    openai.api_key = wee["openai_key"]
    TOKEN = wee["discord_token"]


with open("settings.json") as setty:
    the = json.load(setty)
    chat_channel_ids = the["chat_channels"]
    print(chat_channel_ids)
    server_options = the["server_options"]


def save_settings():
    with open("settings.json", "w") as savey:
        the = {"chat_channels": chat_channel_ids, "server_options": server_options}
        savey.write(json.dumps(the, indent=4))


botintents = discord.Intents(messages=True, message_content=True)
activity = discord.Activity(name="for your questions", type=discord.ActivityType.watching)
client = discord.Client(intents=botintents, activity=activity)
tree = app_commands.CommandTree(client)


chat_memories = {}
image_memories = {}


for idx in chat_channel_ids:
    chat_memories[idx] = ChatMemory()


def isChatChannel(id):
    return id in chat_channel_ids


def addChatChannel(id):
    chat_channel_ids.append(id)
    chat_memories[id] = ChatMemory()
    save_settings()


def verifyChatChannel(id):
    verify = isChatChannel(id)
    if not verify:
        addChatChannel(id)
    return verify


@tenacity.retry(stop=tenacity.stop_after_attempt(3))
async def textwithmem(
    msg: discord.Message, genprompt: str, prepend: str = None
):
    verifyChatChannel(msg.channel.id)

    id = msg.channel.id
    max = 1024
    freq_pen = 0.75
    presence_pen = 0.75
    temp = 0.75

    attachments = msg.attachments
    txtread = ""
    if len(attachments) > 0:
        for attachment in attachments:
            exts = attachment.filename.split(".")

            if exts[-1] in TEXT_EXT:
                txtread = txtread + attachment.filename + "\n" + text.readTxtFile(attachment.url)

    similartext = ""
    similars = vectors.query_similar_text(genprompt, k=2)
    print(similars)
    if len(similars) > 0:
        similartext = "[System] Past messages found in memory. These may not be related to the current conversation.\n"
        for i in range(len(similars)):
            similartext += f"{similars[i][0]}\n\n...\n\n"
    print(similartext)

    genprompt = genprompt + "\n" + txtread  # add text from attachments to message

    if genprompt[len(genprompt) - 1] == " ":
        genprompt = genprompt[:-1]  # remove trailing space for token optimization

    chat_memories[id].add("user", genprompt)

    if len(similartext) > 0:
        chat_memories[id].add("system", similartext)

    messages = chat_memories[id].get()

    res = await text.genchat(
        messages=messages,
        max=max,
        temp=temp,
        freq=freq_pen,
        pres=presence_pen
    )

    generation = res[1]

    if prepend is not None:
        generation = prepend + generation

    # if len(generation) <= 1:
    #     return


    chat_memories[id].add("assistant", generation)

    chat_memories[id].clean()

    # save_usage()

    return ("success", generation)

    # except openai.error.OpenAIError as e:
    #     return e  # not ok...
    # except openai.error.RateLimitError as e:
    #     return e  # not ok...
    # except openai.error.JSONSerializableError as e:
    #     return e  # not ok...
    # except openai
    # except discord.errors.HTTPException as e:
    #     print(e)
    #     return ("fail", e)
    # except Exception as e:
    #     print(e)
    #     return ("fail", e)


@client.event
async def on_ready():
    print("Hi! I'm ready!")


@client.event
async def on_message(message: discord.Message):
    global token_thresh
    global ai_pre_msg
    global ai_name

    idh = message.channel.id

    if message.author.id != client.user.id:
        print("user: ", message.author.name)
        orig = message.content
        print(orig)

        if message.channel.type == discord.ChannelType.private:
            ops = server_options.get(str(message.channel.id), None)
            prepense = server_options[str(message.channel.id)]["start_with"]
            if ops is not None:
                prefix = ops["chat_prefix"]
            if not ops["can_chat"]:
                return
            if prefix is None or message.content.startswith(prefix):
                if prefix is not None:
                    orig = orig[len(prefix):]
                async with message.channel.typing():
                    res = await textwithmem(message, orig)
                    if res[0] == "fail":
                        await message.reply("Sorry, I'm having trouble right now. Please try again.")
                        return
                    await message.reply(res[1])
                    return

        elif orig.startswith("!"):
            orig = orig[1:]  # no !
            argies = orig.split(
                " "
            )  # split by whitespace (not doing this yet actually)
            com = argies.pop(0)  # command is first in split array
            fullprompt = " ".join(argies)
            ops = server_options.get(message.guild.id, None)

            async with message.channel.typing():

                print("command: ", com)
                print("fullprompt: ", fullprompt)

                if com == "sync":
                    # tree.copy_global_to(guild=discord.Object(id=848149296054272000))
                    # tree.copy_global_to(guild=discord.Object(id=1072352297503440936))
                    await tree.sync(guild=discord.Object(id=848149296054272000))
                    await tree.sync(guild=discord.Object(id=1072352297503440936))
                    await tree.sync()
                    return

                if com == "transcribe" or com == "translate" or com == "summarize":
                    valids = ["wav", "mp3", "ogg", "flac", "m4a", "mp4", "webm", "mov"]
                    attachments = message.attachments

                    dl_res = None
                    if len(attachments) > 0 and len(fullprompt) > 0 or len(attachments) > 1:
                        await message.channel.send("Please send only one attachment or link.")
                        return
                    if len(attachments) > 0:
                        exts = attachments[0].filename.split(".")
                        if not exts[-1] in valids:
                            return
                        dl_res = audio.downloadAudio(attachments[0].url, attachments[0].filename)
                    elif len(fullprompt) > 0:
                        validlink = re.search(URL_REGEX, fullprompt)
                        if validlink is None:
                            await message.channel.send("invalid link")
                            return
                        dl_res = audio.downloadYoutubeAudio(fullprompt)

                    if dl_res[0] == "fail":
                        await message.channel.send(f"something went wrong {dl_res[1]}")
                        return
                    # await message.channel.send(f"saved as {dl_res}")
                    if com == "transcribe":
                        asyncio.get_event_loop().create_task(trans.transcriber(message, dl_res[1]))
                    elif com == "translate":
                        asyncio.get_event_loop().create_task(trans.transcriber(message, dl_res[1], task="translate"))
                    elif com == "summarize":
                        res = await trans.transcriber(message, dl_res[1], model_override="small", return_result=True)
                        sum_msg = await message.channel.send("Summarizing...")
                        sum_res = await summarizer.summarizeLongText(res)
                        if (sum_res[0] == "fail"):
                            await sum_msg.delete()
                            await message.channel.send(f"something went wrong {sum_res[1]}")
                            return
                        await sum_msg.delete()
                        await message.reply(sum_res[1])
                    return

                if com == "testytlink":
                    validlink = re.search(URL_REGEX, fullprompt)
                    if validlink is None:
                        await message.channel.send("invalid link")
                        return
                    file = audio.downloadYoutubeAudio(fullprompt)
                    asyncio.get_event_loop().create_task(trans.transcriber(message, file))
                    return

                if com == "ocr":
                    valids = IMG_EXT
                    attachments = message.attachments

                    dl_res = None
                    if len(attachments) > 0:
                        exts = attachments[0].filename.split(".")
                        if not exts[-1] in valids:
                            return
                        dl_res = await images.downloadpic(attachments[0].url)
                    # await message.channel.send(f"saved as {dl_res}")
                    ocr_res = ocr.run_ocr(dl_res)
                    if ocr_res[0] == "fail":
                        await message.channel.send(f"something went wrong {ocr_res[1]}")
                        return
                    elif ocr_res[0] == "text":
                        await message.channel.send(ocr_res[1])
                    elif ocr_res[0] == "file":
                        await message.channel.send(content=ocr_res[1], file=discord.File(ocr_res[2]))
                    return

                if com == "resnet":
                    valids = IMG_EXT
                    attachments = message.attachments

                    dl_res = None
                    if len(attachments) > 0:
                        exts = attachments[0].filename.split(".")
                        if not exts[-1] in valids:
                            return
                        dl_res = await images.downloadpic(attachments[0].url)
                    # await message.channel.send(f"saved as {dl_res}")
                    res = resnet.run_resnet(dl_res)
                    restext = ""
                    for i in res:
                        restext += f"{i[0]}: {round(i[1], 2)}% confidence\n"
                    await message.channel.send(restext)
                    return

                if com == "moderation":
                    res = moderation.classify(fullprompt)
                    if res[0] == "fail":
                        await message.channel.send(f"something went wrong {res[1]}")
                        return
                    await message.reply(res[1])
                    return

        elif idh in chat_channel_ids or idh is None:
            # message.guild.id has to be string bc json won't accept int as key/property name
            ops = server_options.get(str(message.channel.id), None)
            prepense = server_options[str(message.channel.id)]["start_with"]
            if ops is not None:
                prefix = ops["chat_prefix"]
            if not ops["can_chat"]:
                return
            if prefix is None or message.content.startswith(prefix):
                async with message.channel.typing():
                    if prefix is not None:
                        orig = orig[len(prefix):]  # remove prefix
                    ret = await textwithmem(message, genprompt=orig, prepend=prepense)
                    if ret[0] == "fail":
                        await message.channel.send(f"something went wrong {ret[1]}")
                        return
                    await message.reply(ret[1])


def isNotClient():
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.id != client.user.id
    return app_commands.check(predicate)


def serverKnown(id):
    print(id)
    print(id in server_options)
    return id in server_options


def addServer(id):
    server_options[id] = {"can_chat": True, "start_with": "", "chat_prefix": None, "allow_images": True, "system": None, "starter": None}
    return


def verifyServer(id):
    verify = serverKnown(str(id))
    if not verify:
        addServer(str(id))
    return verify


def serverAllowedChat(interaction: discord.Interaction):
    ids = str(interaction.guild.id)
    print(ids)
    print(serverKnown(ids))
    print(server_options[ids]["allow_images"])
    return serverKnown(ids) and server_options[ids]["can_chat"]


def serverAllowedImage(interaction: discord.Interaction):
    ids = str(interaction.guild.id)
    print(ids)
    print(serverKnown(ids))
    print(server_options[ids]["allow_images"])
    return serverKnown(ids) and server_options[ids]["allow_images"]


@tree.command(name="clear", description="Clear the chat history for this channel.")
async def ClearCommand(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)  # think hard
    channelid = interaction.channel_id
    if channelid is None:
        await interaction.followup.send(content="Something bad happened.")
        return
    if channelid in chat_channel_ids:
        chat_memories[channelid].clear()
        await interaction.followup.send(content="i forgor :skull:\nChat memory has been cleared.")
    else:
        await interaction.followup.send(content="Current channel is not a chat channel.")
    return


@tree.command(name="setchat", description="Make this channel a chat channel.")
async def SetChatCommand(interaction: discord.Interaction):
    if interaction.channel_id in chat_channel_ids:
        await interaction.response.send_message(content="This channel is already a chat channel.")
        return
    chat_memories[interaction.channel_id] = ChatMemory()
    chat_channel_ids.append(interaction.channel_id)
    save_settings()
    await interaction.response.send_message(content="This channel is now a chat channel.")
    return


@tree.command(name="unchat", description="Remove chat from this channel.")
async def UnChatCommand(interaction: discord.Interaction):
    if interaction.channel_id not in chat_channel_ids:
        await interaction.response.send_message(content="This channel is not a chat channel.")
        return
    chat_memories.pop(interaction.channel_id)
    chat_channel_ids.remove(interaction.channel_id)
    save_settings()
    await interaction.response.send_message(content="This channel is no longer a chat channel.")
    return


@tree.command(name="system-prompt", description="Set the system prompt for ChatGPT.")
async def SystemPromptCommand(interaction: discord.Interaction, prompt: str = None, noclear: bool = False):
    await interaction.response.defer(thinking=True)  # think hard
    channelid = interaction.channel_id

    if channelid not in chat_channel_ids:
        await interaction.followup.send(content="Current channel is not a chat channel.")
        return

    if prompt is None:
        if chat_memories[channelid].system is not None:
            await interaction.followup.send(content=f"```{chat_memories[channelid].system}```")
            return
        await interaction.followup.send(content="No system prompt set.")
        return

    chat_memories[channelid].setsystem(prompt)
    if len(prompt) > 1900:
        prompt = prompt[:1900] + "{truncated}"
    if not noclear:
        chat_memories[channelid].clear()
    await interaction.followup.send(content=f"System message changed.\n```{prompt}```\nMemory cleared.")
    return


@tree.command(name="starter-message", description="Add a starting assistant message to give context.")
@app_commands.describe(starter="assistant's starting message")
@app_commands.describe(delete="delete the starter message")
@app_commands.describe(noclear="don't clear the chat memory")
async def StarterMessageCommand(interaction: discord.Interaction, starter: str = None, delete: bool = False, noclear: bool = False):
    await interaction.response.defer(thinking=True)  # think hard
    channelid = interaction.channel_id

    if channelid not in chat_channel_ids:
        await interaction.followup.send(content="Current channel is not a chat channel.")
        return

    if delete:
        chat_memories[channelid].setstarter(None)
        await interaction.followup.send(content="Starter message deleted.")
        return

    if starter is None:
        if chat_memories[channelid].starter is not None:
            await interaction.followup.send(content=f"```{chat_memories[channelid].starter}```")
            return
        await interaction.followup.send(content="No starter message set.")
        return

    chat_memories[channelid].setstarter(starter)
    if len(starter) > 1900:
        starter = starter[:1900] + "{truncated}"
    if not noclear:
        chat_memories[channelid].clear()
    await interaction.followup.send(content=f"Starter message changed.\n```{starter}```")
    return


@tree.command(name="setprefix", description="Set the chat prefix for this server.")
@app_commands.describe(prefix="new chat prefix, ideally one character")
async def SetPrefixCommand(interaction: discord.Interaction, prefix: str = None):
    verifyServer(interaction.channel.id)
    if prefix is None:
        await interaction.response.send_message(content="Current prefix: " + server_options[str(interaction.channel.id)]["chat_prefix"])
        return
    if prefix.lower() in ["none", "null", "remove", "delete", "clear"]:
        server_options[str(interaction.channel.id)]["chat_prefix"] = None
        save_settings()
        await interaction.response.send_message(content="Prefix removed.")
        return
    server_options[str(interaction.channel.id)]["chat_prefix"] = prefix
    save_settings()
    await interaction.response.send_message(content=f"Prefix set to `{prefix}`.")
    return


@tree.command(name="startwith", description="Always prepend a response with a certain string.")
@app_commands.describe(startwith="string to prepend")
@app_commands.describe(remove="stops prepending a string")
async def StartWithCommand(interaction: discord.Interaction, startwith: str = None, remove: bool = None):
    if remove is not None and remove is True:
        server_options[str(interaction.guild.id)]["start_with"] = None
        save_settings()
        await interaction.response.send_message(content="Prepended string removed.")
        return
    if startwith is None:
        if server_options[str(interaction.guild.id)]["start_with"] is None:
            await interaction.response.send_message(content="No prepended string.")
            return
        await interaction.response.send_message(content="Current prepended string: " + server_options[str(interaction.guild.id)]["start_with"])
        return
    server_options[str(interaction.guild.id)]["start_with"] = startwith
    save_settings()
    await interaction.response.send_message(content=f"Starting string set to `{startwith}`.")
    return


@tree.command(name="shutdown", description="Shutdown the bot.")
@app_commands.describe(password="get this from the console")
async def ShutdownCommand(interaction: discord.Interaction, password: str = None):
    global internal_password
    if password is None:
        print(f"Someone used /shutdown. Password: {internal_password}")
        await interaction.response.send_message(content="Please provide the password. It was printed in the console.")
        return
    if password != internal_password:
        await interaction.response.send_message(content="Incorrect password.")
        return
    await interaction.response.send_message(content="Shutting down.")
    print("Keyboard interrupt.")
    for channel in chat_channel_ids:
        chat_memories[channel].clear()
        print(f"Cleared {channel}")
    save_settings()
    print("Saved settings")
    print("byeeee")
    await client.close()
    return


@tree.command(name="remove-embed", description="Remove embeddings from the database. Requires the password.")
@app_commands.describe(ids="comma separated list of ids")
@app_commands.describe(password="get this from the console")
async def RemoveEmbedCommand(interaction: discord.Interaction, ids: str = None, password: str = None):
    await interaction.response.defer(thinking=True)  # think hard
    global internal_password
    if password is None:
        await interaction.followup.send(content="Please provide the password. It was printed in the console.")
        return
    if password != internal_password:
        await interaction.followup.send(content="Incorrect password.")
        return
    if ids is None:
        await interaction.followup.send(content="Please provide the ids of the embeddings to remove.")
        return
    ids = ids.split(",")
    try:
        for id in ids:
            id = str(int(id.strip()))
    except ValueError:
        await interaction.followup.send(content="Invalid ids.")
    vectors.remove_local_text(ids)
    vectors.remove_embeddings(ids)
    save_settings()
    await interaction.followup.send(content="Embeddings removed.")
    return


@tree.command(name="temperature", description="Set the temperature of ChatGPT's reponses.")
@app_commands.describe(temperature="new temperature (0.0 - 2.0)")
async def TemperatureCommand(interaction: discord.Interaction, temperature: float = None):
    await interaction.response.defer(thinking=True)  # think hard
    global temp
    if temperature is None:
        await interaction.followup.send(content=f"Current temperature: {temp}")
        return
    newtemp = 0
    try:
        newtemp = float(temperature)
        if newtemp < 0.0 or newtemp > 2.0:
            raise ValueError
    except ValueError:
        await interaction.followup.send(content="Temperature must be a number between 0.0 and 2.0.")
        return
    temp = newtemp
    await interaction.followup.send(content=f"Temperature set to {newtemp}.")
    return
client.run(TOKEN)
