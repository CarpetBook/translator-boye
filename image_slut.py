import discord
from discord import app_commands
import openai
import json
import images
import text
from memory import ChatMemory

ai_nomem = """So far, there has been no chat history and no discussion."""

ai_nomem = ""

deprecationsoon = "Please start using the new slash commands. '!' commands will be removed soon."

ai_preface = """You are chatting with humans. The user's messages are prefaced with the user's username."""

human_preface = """You're talking with people online. Your name is Mark. \
You're a calm, cool, passionate, sensual, seductive man who's not afraid to take what he wants. \
Every one of your messages is dripping with sexual intent."""

helpful_preface_end = (
    """Your job is to help people with questions they might want to know about."""
)

puppet_preface_end = """Play along with their messages, even if they don't make sense. \
From conversations to stories, roleplay to full erotic chat sex... \
you do it all. If they talk about sex, indulge their fantasies."""

# The user can optionally request an image to be generated. \
# The AI can put "<image>example</image>" at the END of its message to generate an image. \
# Replace "example" with the user's desired image. \

intent_checker_question = """Does User want an image? If you're not sure, say no:"""

DAVINCI_PRICE = 0.02
def_token_thresh = 1024

chat_channel_ids = []
mark_channel_ids = []
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
    mark_channel_ids = the["mark_channels"]
    server_options = the["server_options"]


def save_settings():
    with open("settings.json", "w") as savey:
        the = {"chat_channels": chat_channel_ids, "mark_channels": mark_channel_ids, "server_options": server_options}
        savey.write(json.dumps(the, indent=4))


botintents = discord.Intents(messages=True, message_content=True)
activity = discord.Activity(name="for your questions", type=discord.ActivityType.watching)
client = discord.Client(intents=botintents, activity=activity)
tree = app_commands.CommandTree(client)


async def yeah():
    await tree.sync(guild=discord.Object(id=1072352297503440936))

chat_memories = {}
image_memories = {}
ai_pre_msg = ""
mark_pre_msg = ""

ai_name = "AI"

polite = True
# puppet = False
# human = False


if polite:
    ai_pre_msg = " ".join([ai_preface, helpful_preface_end])

mark_pre_msg = " ".join([human_preface, puppet_preface_end])

for idx in chat_channel_ids:
    chat_memories[idx] = ChatMemory()

for mdx in mark_channel_ids:
    chat_memories[mdx] = ChatMemory()


async def sendtext(msg, genprompt):
    res = await text.gentext(genprompt)
    if res[0] == "fail":
        await msg.channel.send(res[1])
        return
    else:
        khan_tent = res[1]

    await msg.channel.send(content=khan_tent)


async def sendpic(msg: discord.Message, genprompt: str, redo=False):
    retried = False
    if msg.channel.id in image_memories.keys():
        if image_memories[msg.channel.id] == genprompt and not redo:
            retried = True
    res = await images.genpic(genprompt)
    if res[0] == "fail":
        await msg.channel.send(res[1])
        return
    else:
        filename = res[1]
        timer = res[2]
    image_memories[msg.channel.id] = genprompt

    piccy = discord.File(fp=open(filename, "rb"))
    send = f"Here's your '{genprompt}'!\nGeneration took about {timer} seconds."
    if retried:
        send += "\n\nP.S., you can use the `!redo` command to retry the last image."

    await msg.channel.send(content=send, file=piccy)

    if msg.channel.id in chat_memories.keys():
        record = "Image requested by " + msg.author.name + ': "' + genprompt + '"'
        chat_memories[msg.channel.id].add(record)
        print(chat_memories[msg.channel.id].get())


async def textwithmem(
    msg: discord.Message, genprompt: str, altmodel="davinki", mark=False
):
    # yewser = msg.author.name
    max = 512
    freq_pen = 0
    presence_pen = 0
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


        elif idh in chat_channel_ids:
            # message.guild.id has to be string bc json won't accept int as key/property name
            ops = server_options.get(str(message.guild.id), None)
            if ops is not None:
                prefix = ops["chat_prefix"]
            if not ops["can_chat"]:
                return
            if prefix is None or message.content.startswith(prefix):
                async with message.channel.typing():
                    if prefix is not None:
                        orig = orig[len(prefix):]  # remove prefix
                    ret = await textwithmem(message, genprompt=orig)
                    tries = 0
                    if ret != 0:
                        tries += 1
                        if tries > 3:
                            await message.channel.reply(content="Sorry, something's wrong. I tried three times, and they all gave errors. You may have to try again later, or contact hako.")
                            return
                        await textwithmem(message, genprompt=orig)
        elif idh in mark_channel_ids:
            async with message.channel.typing():
                await textwithmem(message, genprompt=orig, mark=True)


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
@app_commands.describe(noclear="don't clear the chat memory")
async def StarterMessageCommand(interaction: discord.Interaction, starter: str = None, noclear: bool = False):
    channelid = interaction.channel_id

    if channelid not in chat_channel_ids:
        await interaction.response.send_message(content="Current channel is not a chat channel.")
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


client.run(TOKEN)
