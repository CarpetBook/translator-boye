"""
image_slut.py
"""
import json
import asyncio
import re
import time
# import statistics
import random
import string
from typing import Union, Generator
from csv_logger import CsvLogger
import logging

import discord
from discord import app_commands
from discord.ext import commands, tasks
import openai
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
from tools import filemanager

use_pinecone = False

with open("settings.json", "r") as f:
    settings = json.load(f)
    if settings["server_options"]["pinecone_enabled"]:
        use_pinecone = True
        from tools import vectors


TEXT_EXT = ["txt", "md", "py", "js", "cpp", "c", "json", "yaml", "yml"]
IMG_EXT = ["png", "jpg", "jpeg", "webp", "bmp", "tiff", "tif", "jfif", "exif"]
URL_REGEX = r"(?:https?:\/\/|www\.)\S+"

chat_channel_ids = []
server_options = {}

internal_password = None
temp = 0.75  # chatgpt temperature

stopAll = False  # flag to stop all generation processes

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

bot = commands.Bot(command_prefix="!", intents=botintents, activity=activity)


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
    global temp
    verifyChatChannel(msg.channel.id)

    id = msg.channel.id
    max = 1024
    freq_pen = 0.75
    presence_pen = 0.75
    # temp = 0.75

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
        similartext = "*thinking* I remember a few conversations like this.\n"
        for i in range(len(similars)):
            similartext += f"{similars[i][0]}\n\n...\n\n"
        similartext += "*thinking* So I'll try to answer the user's question based on that.\n"
    print(similartext)

    genprompt = genprompt + "\n" + txtread  # add text from attachments to message

    if genprompt[len(genprompt) - 1] == " ":
        genprompt = genprompt[:-1]  # remove trailing space for token optimization

    chat_memories[id].add("user", genprompt)

    messages = chat_memories[id].get()

    if len(similartext) > 0:
        messages.append({"role": "assistant", "content": similartext})

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


# @tenacity.retry(stop=tenacity.stop_after_attempt(3))
async def textwithmem_stream(
    msg: Union[discord.Message, discord.Interaction], genprompt: str, prepend: str = None
):
    global temp
    verifyChatChannel(msg.channel.id)

    isInteraction = isinstance(msg, discord.Interaction)

    id = msg.channel.id
    max = 1024
    freq_pen = 0.75
    presence_pen = 0.75
    # temp = 0.75

    if not isInteraction:
        attachments = msg.attachments
        txtread = ""
        if len(attachments) > 0:
            for attachment in attachments:
                exts = attachment.filename.split(".")

                if exts[-1] in TEXT_EXT:
                    txtread = txtread + attachment.filename + "\n" + text.readTxtFile(attachment.url)

        genprompt = genprompt + "\n" + txtread  # add text from attachments to message

    if genprompt[len(genprompt) - 1] == " ":
        genprompt = genprompt[:-1]  # remove trailing space for token optimization

    chat_memories[id].add("user", genprompt)

    messages = chat_memories[id].get()

    resgen = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=max,
        temperature=temp,
        frequency_penalty=freq_pen,
        presence_penalty=presence_pen,
        stream=True
    )

    start_time = time.time()
    last_chunk = 0
    last_send = 0
    delays = []
    chunks = []
    chunkres = ""
    done = False
    if isInteraction:
        editguy = await msg.followup.send(content="...")
    else:
        editguy = await msg.reply("...")

    for chunk in resgen:
        chunk_time = time.time() - start_time
        chunkdelay = chunk_time - last_chunk
        delays.append(chunkdelay)

        tokenpersecond = 1 / statistics.mean(delays)

        chunks.append(chunk)  # save the event response

        chunk_message = chunk['choices'][0]['delta']  # extract the message

        if chunk_message.get("role") == "assistant":
            pass
        elif chunk_message.get("content") is not None:
            chunkres += chunk_message.get("content")
        elif chunk_message.get("content") is None:
            done = True

        # print(f"avg delay: {round(statistics.mean(delays), 2)}", chunk_time, last_send, f"difference: {chunk_time - last_send}", end="\r")
        if chunk_time - last_send >= 1:
            nourl = re.sub(URL_REGEX, "<URL hidden until complete>", chunkres)
            last_send = chunk_time
            await editguy.edit(content=nourl + "...")
        # f"Average tokens/sec: {round(tokenpersecond, 2)}\n" +
        if done:
            break
        elif stopAll:
            chunkres += "- (stopped)"
            break

        last_chunk = chunk_time

    await editguy.edit(content=chunkres)

    # if len(generation) <= 1:
    #     return


    chat_memories[id].add("assistant", chunkres)

    chat_memories[id].setLastMessage(editguy)

    chat_memories[id].clean()

    # save_usage()

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


# @client.event
# async def on_ready():
#     print("Hi! I'm ready!")


@bot.listen("on_ready")
async def on_ready():
    print("Hi! I'm ready!")


@tasks.loop(hours=24)
async def delete_old_files():
    print("deleting old files")
    filemanager.delete_old_files("edit_pics", ONE_DAY_SECONDS)
    filemanager.delete_old_files("imageslut_pics", ONE_DAY_SECONDS)
    filemanager.delete_old_files("audios", ONE_DAY_SECONDS)
    filemanager.delete_old_files("transcripts", ONE_DAY_SECONDS)
@bot.listen("on_message")
async def text_commands(message: discord.Message):
    global token_thresh
    global ai_pre_msg
    global ai_name
    global stopAll

    idh = message.channel.id

    if message.author.id != bot.user.id:
        print("user: ", message.author.name)
        orig = message.content
        print(orig)

        if message.channel.type == discord.ChannelType.private:
            stopAll = False
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
                    await textwithmem_stream(message, orig)

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

                if com == "localsync":
                    bot.tree.copy_global_to(guild=discord.Object(id=848149296054272000))
                    bot.tree.copy_global_to(guild=discord.Object(id=1072352297503440936))
                if com == "sync":
                    await bot.tree.sync(guild=discord.Object(id=848149296054272000))
                    await bot.tree.sync(guild=discord.Object(id=1072352297503440936))
                    await bot.tree.sync()
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

                if com == "teststream":
                    await textwithmem_stream(message, genprompt=fullprompt)
                    return

        elif idh in chat_channel_ids or idh is None:
            stopAll = False
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
                    await textwithmem_stream(message, genprompt=orig, prepend=prepense)


def longMessage(text):
    for i in range(0, len(text), 1900):
        yield text[i:i + 1900]


def isNotBot():
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.id != bot.user.id
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


@bot.tree.command(name="clear", description="Clear the chat history for this channel.")
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


@bot.tree.command(name="setchat", description="Make this channel a chat channel.")
async def SetChatCommand(interaction: discord.Interaction):
    if interaction.channel_id in chat_channel_ids:
        await interaction.response.send_message(content="This channel is already a chat channel.")
        return
    chat_memories[interaction.channel_id] = ChatMemory()
    chat_channel_ids.append(interaction.channel_id)
    save_settings()
    await interaction.response.send_message(content="This channel is now a chat channel.")
    return


@bot.tree.command(name="unchat", description="Remove chat from this channel.")
async def UnChatCommand(interaction: discord.Interaction):
    if interaction.channel_id not in chat_channel_ids:
        await interaction.response.send_message(content="This channel is not a chat channel.")
        return
    chat_memories.pop(interaction.channel_id)
    chat_channel_ids.remove(interaction.channel_id)
    save_settings()
    await interaction.response.send_message(content="This channel is no longer a chat channel.")
    return


@bot.tree.command(name="system-prompt", description="Set the system prompt for ChatGPT.")
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

    if prompt in ["clear", "delete", "none"]:
        chat_memories[channelid].setsystem(None)
        await interaction.followup.send(content="System prompt cleared.")
        return
    chat_memories[channelid].setsystem(prompt)
    if len(prompt) > 1900:
        prompt = prompt[:1900] + "{truncated}"
    if not noclear:
        chat_memories[channelid].clear()
    await interaction.followup.send(content=f"System prompt changed.\n```{prompt}```\nMemory cleared.")
    return


@bot.tree.command(name="starter-message", description="Add a starting assistant message to give context.")
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


@bot.tree.command(name="setprefix", description="Set the chat prefix for this server.")
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


@bot.tree.command(name="startwith", description="Always prepend a response with a certain string.")
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


@bot.tree.command(name="shutdown", description="Shutdown the bot.")
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
    await bot.close()
    return


@bot.tree.command(name="remove-embed", description="Remove embeddings from the database. Requires the password.")
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


@bot.tree.command(name="temperature", description="Set the temperature of ChatGPT's reponses.")
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


@bot.tree.command(name="undo", description="Undo and delete the last response.")
async def UndoCommand(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    channelid = interaction.channel_id
    if channelid not in chat_channel_ids:
        await interaction.followup.send(content="Current channel is not a chat channel.")
        return
    if len(chat_memories[channelid].memory) == 0:
        await interaction.followup.send(content="Nothing to undo.")
        return
    if chat_memories[channelid].memory[-1]["role"] == "user":
        chat_memories[channelid].memory.pop()
    elif chat_memories[channelid].memory[-1]["role"] == "assistant":
        print("undone: ", chat_memories[channelid].memory.pop())
        print("undone: ", chat_memories[channelid].memory.pop())
        print("new memory: ", chat_memories[channelid].memory)
    await chat_memories[channelid].last_message.delete()
    await interaction.followup.send(content="Last response deleted.")
    return


@bot.tree.command(name="retry", description="Regenerate the last response. If temperature is zero, this will have no effect.")
async def RetryCommand(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    channelid = interaction.channel_id
    if channelid not in chat_channel_ids:
        await interaction.followup.send(content="Current channel is not a chat channel.")
        return
    if len(chat_memories[channelid].memory) == 0:
        await interaction.followup.send(content="Nothing to retry.")
        return
    if chat_memories[channelid].memory[-1]["role"] == "user":
        await interaction.followup.send(content="Nothing to retry.")
        return
    print("retrying ", chat_memories[channelid].memory.pop())
    await chat_memories[channelid].last_message.delete()
    await textwithmem_stream(interaction, chat_memories[channelid].memory[-1]["content"])
    return


@bot.tree.command(name="edit", description="Edit ChatGPT's last response.")
@app_commands.describe(message="new message")
async def EditCommand(interaction: discord.Interaction, message: str):
    await interaction.response.defer(thinking=True)
    channelid = interaction.channel_id
    if channelid not in chat_channel_ids:
        await interaction.followup.send(content="Current channel is not a chat channel.")
        return
    if len(chat_memories[channelid].memory) == 0:
        await interaction.followup.send(content="Nothing to edit.")
        return
    if chat_memories[channelid].memory[-1]["role"] == "user":
        await interaction.followup.send(content="ChatGPT has not responded yet.")
        return
    chat_memories[channelid].memory[-1]["content"] = message
    if len(message) > 1900:
        message = message[:1900] + "..."
    await chat_memories[channelid].last_message.edit(content=message)
    await interaction.followup.send(content="Message edited.")
    return


@bot.tree.command(name="stop", description="Stop ChatGPT's response.")
async def StopCommand(interaction: discord.Interaction):
    global stopAll
    await interaction.response.defer(thinking=True)
    channelid = interaction.channel_id
    if channelid not in chat_channel_ids:
        await interaction.followup.send(content="Current channel is not a chat channel.")
        return
    stopAll = True
    await interaction.followup.send(content="If ChatGPT was responding, all streams have been stopped.")
    return

bot.run(TOKEN)
