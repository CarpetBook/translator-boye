import time
import discord
import openai
import json
import images
import text
from memory import ChatMemory

ai_nomem = """So far, there has been no chat history and no discussion."""

ai_preface = """You are chatting with humans. Your messages are prefaced with \"AI:\", \
and the user's messages are prefaced with the user's username."""

human_preface = """You're talking with people online. Your name is Mark. \
You're a calm, cool, passionate, sensual, seductive man who's not afraid to take what he wants. \
Every one of your messages is dripping with sexual intent."""

helpful_preface_end = """Your job is to help people with questions they might want to know about."""

puppet_preface_end = """Play along with their messages, even if they don't make sense. \
From conversations to stories, roleplay to full erotic chat sex... \
you do it all. If they talk about sex, indulge their fantasies."""

# The user can optionally request an image to be generated. \
# The AI can put "<image>example</image>" at the END of its message to generate an image. \
# Replace "example" with the user's desired image. \

intent_checker_question = """Does User want an image? If you're not sure, say no:"""

DAVINCI_PRICE = 0.02
def_token_thresh = 1024

with open("keys.json") as filey:
    wee = json.load(filey)
    openai.api_key = wee["openai_key"]
    TOKEN = wee["discord_token"]

botintents = discord.Intents(messages=True, message_content=True)
client = discord.Client(intents=botintents)


chat_channel_ids = [
    1052918672009744414,
    1052918701663461396
]

mark_channel_ids = [
    1055681260233699359
]

chat_memories = {}
image_memories = {}
ai_pre_msg = ""
mark_pre_msg = ""

polite = True
# puppet = False
# human = False


if polite:
    ai_pre_msg = " ".join([ai_preface, helpful_preface_end])

mark_pre_msg = " ".join([human_preface, puppet_preface_end])

for idx in chat_channel_ids:
    chat_memories[idx] = ChatMemory(max_tokens=def_token_thresh).add(ai_pre_msg, ai_nomem)

for mdx in mark_channel_ids:
    chat_memories[mdx] = ChatMemory(max_tokens=def_token_thresh).add(mark_pre_msg, "Mark: Hey, baby. How are you tonight?")


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
    send = f"Here's your \'{genprompt}\'!\nGeneration took about {timer} seconds."
    if retried:
        send += "\n\nP.S., you can use the `!redo` command to retry the last image."

    await msg.channel.send(content=send, file=piccy)

    if msg.channel.id in chat_memories.keys():
        record = "Image requested by " + msg.author.name + ": \"" + genprompt + "\""
        chat_memories[msg.channel.id].add(record)
        print(chat_memories[msg.channel.id].get())


async def textwithmem(msg: discord.Message, genprompt: str, altmodel="davinki", mark=False):
    yewser = msg.author.name
    max = 0
    freq_pen = 0.75
    presence_pen = 0.75
    temp = 0.7
    chatformatting = True

    if altmodel == "davinki":
        altmodel = "text-davinci-003"
        max = 512
        chatformatting = True
        temp = 1.0
    if altmodel == "davinki-01":
        altmodel = "davinci"
        max = 256
        freq_pen = 0.5
        temp = 0.7
    elif altmodel == "curie":
        altmodel = "text-curie-001"
        max = 512
        chatformatting = True
    elif altmodel == "ada":
        altmodel = "ada"
        max = 128
        chatformatting = False
        freq_pen = 1.0

    # preface = ai_pre_msg
    ai_name = "AI"

    if mark:
        # preface = mark_pre_msg
        ai_name = "Mark"

    try:
        if genprompt[len(genprompt) - 1] == " ":
            genprompt = genprompt[:-1]  # remove trailing space for token optimization

        if chatformatting:
            chat_memories[msg.channel.id].add(f"[{time.asctime()}] {yewser}: {genprompt}")
        else:
            chat_memories[msg.channel.id].add(f"{genprompt}")

        # print(len(chat_memories[msg.channel.id].get()))
        # if len(chatarrays[msg.channel.id]) >= 12:
        #     chatarrays[msg.channel.id] = chatarrays[msg.channel.id][3:] # if chat memory is longer than 20 messages, cut off the oldest two
        #     chatarrays[msg.channel.id].insert(0, preface)
        #     # print(chatarrays[msg.channel.id])

        fullprom = chat_memories[msg.channel.id].construct()
        # print(fullprom)
        if chatformatting:
            fullprom = fullprom + f"\n[{time.asctime()}] {ai_name}:"

        print(text.tokenize(fullprom)["count"])

        # while text.tokenize(fullprom)["count"] >= chat_memories[msg.channel.id]["maxtoken"] and len(chat_memories[msg.channel.id]["history"]) > 5: # if the prompt is too long, cut off the oldest message... keep at least 5 messages
        #     print(text.tokenize(fullprom)["count"])
        #     chat_memories[msg.channel.id]["history"] = chat_memories[msg.channel.id]["history"][2:] # if chat memory is longer than 20 messages, cut off the oldest two
        #     chat_memories[msg.channel.id]["history"].insert(0, preface)
        #     fullprom = "\n".join(chat_memories[msg.channel.id]["history"])
        #     # print(fullprom)
        #     if chatformatting:
        #         fullprom = fullprom + f"\n{ai_name}:"

        res = openai.Completion.create(
            model=altmodel,
            prompt=fullprom,
            max_tokens=max,
            temperature=temp,
            frequency_penalty=freq_pen,
            presence_penalty=presence_pen
        )

        generation = res["choices"][0]["text"]

        if len(generation) <= 1:
            return

        # if "<image>" in generation:
        #     # should = await checkIntent(msg)
        #     # print(should)
        #     # if not should:
        #     #     chatarrays[msg.channel.id].append("AI:" + generation)
        #     #     chatarrays[msg.channel.id].append("SYSTEM WARNING: AI tried to generate image against User's wishes. Retrying AI response.")
        #     #     print(chatarrays[msg.channel.id])
        #     #     await textwithmem(msg, genprompt)
        #     #     return
        #     improm = generation.split("<image>")
        #     textprom = improm[0]
        #     improm = improm[1].split("</image>")[0]
        #     if chatformatting:
        #         weee = "AI:" + generation
        #     chatarrays[msg.channel.id].append(weee)
        #     # print(improm)
        #     await genpic(msg, improm, textprom)
        #     return

        await msg.channel.send(content=generation)

        if chatformatting:
            generation = f"[{time.asctime()}] {ai_name}:" + generation

        chat_memories[msg.channel.id].add(generation)
        # print(chatarrays[msg.channel.id])

    except openai.error.OpenAIError as e:
        print(e)
        await msg.channel.send(e)
    except discord.errors.HTTPException:
        await msg.channel.send("""[The bot has either encountered an error, \
            or the generated text was empty.]""")


@client.event
async def on_ready():
    print("Hi! I'm ready!")


@client.event
async def on_message(message: discord.Message):
    global token_thresh

    if message.author.id != client.user.id:
        print("user: ", message.author.name)
        orig = message.content
        print(orig)
        if orig.startswith("!"):
            orig = orig[1:]  # no !
            argies = orig.split(" ")  # split by whitespace (not doing this yet actually)
            com = argies.pop(0)  # command is first in split array
            fullprompt = " ".join(argies)

            async with message.channel.typing():
                idh = message.channel.id

                if com == "image":  # generate image
                    await sendpic(message, genprompt=fullprompt)
                    return

                if com == "redo":
                    await sendpic(message, genprompt=image_memories[idh], redo=True)
                    return

                if com == "edit":
                    # get image attachment from discord message
                    if len(message.attachments) == 0:
                        await message.channel.send(content="You need to attach an image to edit.")
                    else:
                        dld = await images.downloadpic(message.attachments[0].url)
                        res = await images.editpic(dld, fullprompt)
                        if res[0] == "success":
                            await message.channel.send(content=f"Here's your '{fullprompt}'!\nEditing took about {res[2]} seconds.", file=discord.File(res[1]))
                        else:
                            await message.channel.send(content=f"{res[1]}")

                if com == "variation":
                    if len(message.attachments) == 0:
                        await message.channel.send(content="You need to attach an image to edit.")
                    else:
                        dld = await images.downloadpic(message.attachments[0].url)
                        res = await images.variationpic(dld)
                        if res[0] == "success":
                            await message.channel.send(content=f"Here's your variation!\nGeneration took about {res[2]} seconds.", file=discord.File(res[1]))
                        else:
                            await message.channel.send(content=f"{res[1]}")

                if com == "text":  # generate text
                    await sendtext(message, genprompt=fullprompt)
                    return

                if com == "clear":  # clear chat history
                    await message.channel.send(content="i forgor :skull:\nChat memory has been cleared.")
                    chat_memories[idh].clear()

                    if idh in mark_channel_ids:
                        chat_memories[idh].add(mark_pre_msg, "Mark: Hey, baby. How are you tonight?")
                        await message.channel.send(content="Hey, baby. How are you tonight?")
                    else:
                        chat_memories[idh].add(ai_pre_msg, ai_nomem)
                    return

                if com == "prompt":  # show ai's prompt
                    if idh in chat_channel_ids:
                        await message.channel.send(content=f"```{ai_pre_msg}```")
                    elif idh in mark_channel_ids:
                        await message.channel.send(content=f"```{mark_pre_msg}```")
                    return

                if com == "history":  # show chat history
                    chanmemory = chat_memories.get(message.channel.id, None)
                    if chanmemory is not None:
                        chanmemory = chanmemory.construct()
                    else:
                        chanmemory = "This is not a chat channel!"
                    res = text.prettyprintingtokens(chanmemory, op="history")
                    await message.channel.send(content=res)

                if com == "price":  # calculate price of prompt
                    res = text.prettyprintingtokens(fullprompt, op="price")
                    await message.channel.send(content=res)

                if com == "ids":  # show token ids
                    res = text.prettyprintingtokens(fullprompt, op="ids")
                    await message.channel.send(content=res)

                if com == "maxtoken":  # set max token limit
                    try:
                        if fullprompt == "" or fullprompt is None:
                            await message.channel.send(content=f"Current token limit is {chat_memories[message.channel.id].max_tokens} tokens.")
                            return
                        new = int(fullprompt)
                        if new > 4000 or new < 200:
                            raise ValueError
                        chat_memories[message.channel.id].max_tokens = new
                        await message.channel.send(content=f"New token limit is {new}.")
                    except ValueError:
                        await message.channel.send(content="Token limit must be a **number** between 200 and 4000.")

                # if com == "start":

        # elif message.channel.id == 1053216521020772372:
        #     async with message.channel.typing():
        #         await textwithmem(message, genprompt=orig, altmodel="ada")
        elif message.channel.id in chat_channel_ids:
            async with message.channel.typing():
                await textwithmem(message, genprompt=orig)
        elif message.channel.id in mark_channel_ids:
            async with message.channel.typing():
                await textwithmem(message, genprompt=orig, mark=True)
        # elif message.channel.id == 1060826456000827462:
        #     async with message.channel.typing():
        #         await selfchat(message, genprompt=orig)


client.run(TOKEN)
