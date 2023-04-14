import requests
import openai
import json
import time


def chat(
    model: str = "gpt-3.5-turbo",
    messages: dict = None,
    max_tokens: int = 512,
    temperature: float = 0,
    frequency_penalty: float = 0,
    presence_penalty: float = 0
):
    chaturl = "https://api.openai.com/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + openai.api_key}
    data = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "frequency_penalty": frequency_penalty,
        "presence_penalty": presence_penalty
    }

    start = time.time()
    res = requests.post(chaturl, headers=headers, json=data)
    end = time.time()

    print(f"[Requester] Time to respond: {end - start} seconds")

    if res.status_code != 200:
        return ("fail", res.status_code)
    else:
        return ("success", res.json())


if __name__ == "__main__":
    with open("keys.json") as filey:
        wee = json.load(filey)
        openai.api_key = wee["openai_key"]
    messages = [{"role": "user", "content": "Hello"}]
    chat(messages=messages)
