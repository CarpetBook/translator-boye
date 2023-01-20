import openai
from transformers import GPT2TokenizerFast

tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

DAVINCI_PRICE = 0.02

async def gentext(genprompt, no_prompt=False):
    try:
        if genprompt[len(genprompt)-1] == " ":
            genprompt = genprompt[:-1] # remove trailing space for token optimization

        res = openai.Completion.create(
                model="text-davinci-003",
                prompt=genprompt,
                max_tokens=512,
                temperature=0.75
                )
        
        generation = res["choices"][0]["text"]
        khan_tent = generation
        if not no_prompt:
            khan_tent = f"**{genprompt}**" + khan_tent
        
        return ("success", khan_tent)
    except openai.error.OpenAIError as e:
        return ("fail", e)


def tokenize(text: str) -> object:
    tok = tokenizer(text)["input_ids"]
    cnt = len(tok)
    return {"tokens": tok, "count": cnt}

def decode(tokens: list) -> str:
    text = tokenizer.decode(tokens)


def prettyprintingtokens(text: str, op="history") -> str:
    res = tokenize(text)
    count = res["count"]
    ids = res["tokens"]
    price = (count/1000) * DAVINCI_PRICE
    memfull = round( (count/4000) * 100, 0)

    if len(text) > 1700:
        text = text[:1700] + "\n[truncated due to Discord character limit]"
    pretty = ""
    if op == "price":
        pretty = f"```{text}```Text is {count} tokens.\nThis prompt costs approximately ${format(price, '.5f')}."
        pretty = pretty + f"\nThe entire prompt would occupy about {memfull:.0f}% of the AI's memory."
    if op == "ids":
        id_strs = []
        for idx in range(len(ids)):
            id_strs.append(str(ids[idx]))
        tok = ", ".join(id_strs)
        pretty = f"```{tok}```"
    if op == "history":
        pretty = f"```{text}```Chat history contains {count} tokens.\nThe next message will cost approximately ${format(price, '.5f')} to generate."
        pretty = pretty + f"\nThe chat history currently occupies about {memfull:.0f}% of the AI's memory."
    
    return pretty