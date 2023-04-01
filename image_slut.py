import discord
from discord import app_commands
import openai
import json
import text
import audio
import trans
from memory import ChatMemory

import asyncio

TEXT_EXT = ["txt", "md", "py", "js", "cpp", "c", "json", "yaml", "yml"]

chat_channel_ids = []
server_options = {}

with open("keys.json") as filey:
    wee = json.load(filey)
    openai.api_key = wee["openai_key"]
    # TOKEN = wee["discord_token"]
    TOKEN = "MTA3NzY4MTQ4MTIyMjIwMTM1NA.GWMfBn.brY5jQbK_4BKi0HQoaFz-7cX5KswqNqOZL73Ro"


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


async def textwithmem(
    msg: discord.Message, genprompt: str, prepend: str = None
):
    # yewser = msg.author.name
    max = 1024
    freq_pen = 0.75
    presence_pen = 0.75
    temp = 0.75

    try:
        if genprompt[len(genprompt) - 1] == " ":
            genprompt = genprompt[:-1]  # remove trailing space for token optimization

        chat_memories[msg.channel.id].add("user", genprompt)

        messages = chat_memories[msg.channel.id].get()

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

        await msg.reply(content=generation)

        chat_memories[msg.channel.id].add("assistant", generation)

        chat_memories[msg.channel.id].clean()

        return 0  # ok

    except openai.error.OpenAIError as e:
        return e  # not ok...
    except openai.error.RateLimitError as e:
        return e  # not ok...
    except discord.errors.HTTPException:
        await msg.channel.send(
            """[The bot has either encountered an error, \
            or the generated text was empty.]"""
        )


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
        if orig.startswith("!"):
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
                    tree.copy_global_to(guild=discord.Object(id=848149296054272000))
                    tree.copy_global_to(guild=discord.Object(id=1072352297503440936))
                    await tree.sync(guild=discord.Object(id=848149296054272000))
                    await tree.sync(guild=discord.Object(id=1072352297503440936))
                    await tree.sync()
                    return

                if com == "downloadtest" or com == "transcribe" or com == "translate":
                    valids = ["wav", "mp3", "ogg", "flac", "m4a", "mp4", "webm", "mov"]
                    attachments = message.attachments
                    if len(attachments) > 0:
                        for attachment in attachments:
                            exts = attachment.filename.split(".")
                            if not exts[-1] in valids:
                                return
                    dl_res = audio.downloadAudio(message.attachments[0].url, exts[-1])
                    if dl_res[0] == "fail":
                        await message.channel.send(f"something went wrong {dl_res[1]}")
                        return
                    # await message.channel.send(f"saved as {dl_res}")
                    if com == "transcribe":
                        asyncio.get_event_loop().create_task(trans.transcriber(message, dl_res[1]))
                    elif com == "translate":
                        asyncio.get_event_loop().create_task(trans.transcriber(message, dl_res[1], task="translate"))
                    return


        elif idh in chat_channel_ids:
            # message.guild.id has to be string bc json won't accept int as key/property name
            attachments = message.attachments
            txtread = ""
            if len(attachments) > 0:
                for attachment in attachments:
                    exts = attachment.filename.split(".")
                    print(exts)
                    print(attachment.filename)
                    print(exts[-1])
                    print(exts[-1] in TEXT_EXT)
                    if exts[-1] in TEXT_EXT:
                        txtread = txtread + attachment.filename + "\n" + text.readTxtFile(attachment.url)
            orig = message.content + \
                " " + txtread  # add text from attachments to message
            ops = server_options.get(str(message.guild.id), None)
            prepense = server_options[str(message.guild.id)]["start_with"]
            if ops is not None:
                prefix = ops["chat_prefix"]
            if not ops["can_chat"]:
                return
            if prefix is None or message.content.startswith(prefix):
                async with message.channel.typing():
                    if prefix is not None:
                        orig = orig[len(prefix):]  # remove prefix
                    ret = await textwithmem(message, genprompt=orig, prepend=prepense)
                    tries = 0
                    if ret != 0:
                        tries += 1
                        if tries > 3:
                            await message.channel.reply(content="Sorry, something's wrong. I tried three times, and they all gave errors. You may have to try again later, or contact hako.")
                            return
                        await textwithmem(message, genprompt=orig, prepend=prepense)


def isNotClient():
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.id != client.user.id
    return app_commands.check(predicate)


def serverKnown(guild_id):
    print(guild_id)
    print(guild_id in server_options)
    return guild_id in server_options


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
    channelid = interaction.channel_id
    if channelid is None:
        await interaction.response.send_message(content="Something bad happened.")
        return
    if channelid in chat_channel_ids:
        chat_memories[channelid].clear()
        await interaction.response.send_message(content="i forgor :skull:\nChat memory has been cleared.")
    else:
        await interaction.response.send_message(content="Current channel is not a chat channel.")
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
    channelid = interaction.channel_id

    if channelid not in chat_channel_ids:
        await interaction.response.send_message(content="Current channel is not a chat channel.")
        return

    if prompt is None:
        if chat_memories[channelid].system is not None:
            await interaction.response.send_message(content=f"```{chat_memories[channelid].system}```")
            return
        await interaction.response.send_message(content="No system prompt set.")
        return

    chat_memories[channelid].setsystem(prompt)
    if len(prompt) > 1900:
        prompt = prompt[:1900] + "{truncated}"
    if not noclear:
        chat_memories[channelid].clear()
    await interaction.response.send_message(content=f"System message changed.\n```{prompt}```\nMemory cleared.")
    return


@tree.command(name="starter-message", description="Add a starting assistant message to give context.")
@app_commands.describe(starter="assistant's starting message")
@app_commands.describe(delete="delete the starter message")
@app_commands.describe(noclear="don't clear the chat memory")
async def StarterMessageCommand(interaction: discord.Interaction, starter: str = None, delete: bool = False, noclear: bool = False):
    channelid = interaction.channel_id

    if channelid not in chat_channel_ids:
        await interaction.response.send_message(content="Current channel is not a chat channel.")
        return

    if delete:
        chat_memories[channelid].setstarter(None)
        await interaction.response.send_message(content="Starter message deleted.")
        return

    if starter is None:
        if chat_memories[channelid].starter is not None:
            await interaction.response.send_message(content=f"```{chat_memories[channelid].starter}```")
            return
        await interaction.response.send_message(content="No starter message set.")
        return

    chat_memories[channelid].setstarter(starter)
    if len(starter) > 1900:
        starter = starter[:1900] + "{truncated}"
    if not noclear:
        chat_memories[channelid].clear()
    await interaction.response.send_message(content=f"Starter message changed.\n```{starter}```")
    return


@tree.command(name="setprefix", description="Set the chat prefix for this server.")
@app_commands.describe(prefix="new chat prefix, ideally one character")
async def SetPrefixCommand(interaction: discord.Interaction, prefix: str = None):
    if prefix is None:
        await interaction.response.send_message(content="Current prefix: " + server_options[str(interaction.guild.id)]["chat_prefix"])
        return
    server_options[str(interaction.guild.id)]["chat_prefix"] = prefix
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

client.run(TOKEN)
