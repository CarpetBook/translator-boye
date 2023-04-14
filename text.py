import openai
import requests
import requester
# import random
# from transformers import GPT2TokenizerFast

# tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

DAVINCI_PRICE = 0.02


async def gentext(genprompt, no_prompt=False, **kwargs):
    try:
        if genprompt[len(genprompt) - 1] == " ":
            genprompt = genprompt[:-1]  # remove trailing space for token optimization

        res = openai.Completion.create(
            model="text-davinci-003", prompt=genprompt, *kwargs
        )

        generation = res["choices"][0]["text"]
        khan_tent = generation
        if not no_prompt:
            khan_tent = f"**{genprompt}**" + khan_tent

        return ("success", khan_tent)
    except openai.error.OpenAIError as e:
        return ("fail", e)


async def genchat(messages, max=512, temp=0, freq=1, pres=1):
    try:
        print(messages)
        res = requester.chat(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=max,
            temperature=temp,
            frequency_penalty=freq,
            presence_penalty=pres
        )
        res = res[1]
        print(res)
        generation = res['choices'][0]['message']['content']
        return ("success", generation)
    except Exception as e:
        return ("fail", e)


def readTxtFile(attachmenturl):
    try:
        r = requests.get(attachmenturl)
        return r.text
    except requests.exceptions.RequestException as e:
        print(f"Something about a provided text file was malformed, or the request failed. {e}")
        return None

# def decode(tokens: list) -> str:
#     text = tokenizer.decode(tokens)


# def prettyprintingtokens(text: str, op="history") -> str:
#     res = tokenize(text)
#     count = res["count"]
#     ids = res["tokens"]
#     price = (count / 1000) * DAVINCI_PRICE
#     memfull = round((count / 4000) * 100, 0)

#     if len(text) > 1700:
#         text = text[:1700] + "\n[truncated due to Discord character limit]"
#     pretty = ""
#     if op == "price":
#         pretty = f"```{text}```Text is {count} tokens.\nThis prompt costs approximately ${format(price, '.5f')}."
#         pretty = (
#             pretty
#             + f"\nThe entire prompt would occupy about {memfull:.0f}% of the AI's memory."
#         )
#     if op == "ids":
#         id_strs = []
#         for idx in range(len(ids)):
#             id_strs.append(str(ids[idx]))
#         tok = ", ".join(id_strs)
#         pretty = f"```{tok}```"
#     if op == "history":
#         pretty = f"```{text}```Chat history contains {count} tokens.\nThe next message will cost approximately ${format(price, '.5f')} to generate."
#         pretty = (
#             pretty
#             + f"\nThe chat history currently occupies about {memfull:.0f}% of the AI's memory."
#         )

#     return pretty


# def randomtokens(numtokens):
#     return tokenizer.decode(random.choices(range(50257), k=numtokens))


# def compressChr(text):
#     text = text.replace(".", "<|endoftext|>")
#     tokens = tokenizer.encode(text)
#     return "".join([chr(i) for i in tokens])


# def decompressChr(text):
#     tokens = [ord(i) for i in text]
#     text = tokenizer.decode(tokens)
#     return text.replace("<|endoftext|>", ".")
