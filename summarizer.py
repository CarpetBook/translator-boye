import text
import tiktoken

tik = tiktoken.get_encoding("cl100k_base")


async def summarizeLongText(longtext: str):
    tokens = tik.encode(longtext, disallowed_special=())

    chunks = [tokens[i : i + 2048] for i in range(0, len(tokens), 2048)]

    summaries = []
    for chunk in chunks:
        chunk = tik.decode(chunk)
        res = await summarizeChunk(chunk)
        if res[0] == "fail":
            return ("fail", res[1])
        summaries.append(res[1])

    if len(summaries) == 1:
        return ("success", summaries[0])

    totalres = await summarizeAllChunks(summaries)

    if totalres[0] == "fail":
        return ("fail", totalres[1])
    return ("success", totalres[1])


async def summarizeChunk(sumtext: str):
    messages = [
        {"role": "user", "content": f"Summarize the following captions. Give ample details.\n{sumtext}"}
    ]

    res = await text.genchat(
        messages,
        max=1024
    )

    if res[0] == "fail":
        return ("fail", res[1])
    return ("success", res[1])


async def summarizeAllChunks(chunks: list):
    all = "\n".join(chunks)
    messages = [
        {"role": "user", "content": f"Combine the following summaries. {all}"}
    ]

    # for chunk in chunks[::-1]:
    #     messages.insert(0, {"role": "user", "content": chunk})

    res = await text.genchat(
        messages,
        max=1024
    )

    if res[0] == "fail":
        return ("fail", res[1])
    return ("success", res[1])
