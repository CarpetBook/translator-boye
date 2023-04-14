import openai
import pinecone
import pickle
import json
from typing import Union

import tiktoken
tik = tiktoken.get_encoding("cl100k_base")

local_db = None
try:
    with open("local_chatgpt_ltm.pickle", "rb") as f:
        local_db = pickle.load(f)
except FileNotFoundError:
    local_db = {}
    with open("local_chatgpt_ltm.pickle", "wb") as f:
        pickle.dump(local_db, f)
except Exception:
    for i in range(20):
        print("[CRITICAL] something went horribly wrong while loading/creating local db pickle", end=" ")

with open("keys.json") as filey:
    wee = json.load(filey)
    openai.api_key = wee["openai_key"]
    pinecone.init(api_key=wee["pinecone_key"], environment=wee["pinecone_env"])

ind = pinecone.list_indexes()
pine_db = pinecone.Index(index_name=ind[0])


def save_local_db_pickle():
    with open("local_chatgpt_ltm.pickle", "wb") as f:
        pickle.dump(local_db, f)

    with open("local_chatgpt_ltm.json", "w") as f:
        json.dump(local_db, f, indent=4)


def embed(text: Union[str, list]):
    collection = text
    if isinstance(text, str):
        collection = [text]

    allpassagetoken = []
    for passage in collection:
        passagetoken = tik.encode(passage, disallowed_special=())
        if len(passagetoken) > 8192:
            passagetoken = passagetoken[:8192]
        allpassagetoken.append(passagetoken)

    res = openai.Embedding.create(
        model="text-embedding-ada-002",
        input=allpassagetoken
    )
    return [i["embedding"] for i in res["data"]]


def upsert_embeddings(ids: list, vectors: list, namespace: str = None):
    global pine_db
    if len(vectors) != len(ids):
        raise ValueError("Vectors and ids must be the same length")
    formatted = zip(ids, vectors)
    pine_db.upsert(formatted, namespace=namespace)


def upsert_local_text(ids: list, texts: list):
    global local_db
    if len(ids) != len(texts):
        raise ValueError("Ids and texts must be the same length")
    for id, text in zip(ids, texts):
        local_db[id] = text
    save_local_db_pickle()


def save_longterm_text(texts: list, namespace: str = "translator-boye"):
    global local_db

    ids = [str(len(local_db) + i) for i in range(len(texts))]
    if len(local_db) == 0:
        ids = ["0"]
    upsert_local_text(ids, texts)

    vecs = embed(texts)
    upsert_embeddings(ids, vecs, namespace=namespace)


def query_similar_text(text: str, namespace: str = "translator-boye"):
    global pine_db
    vec = embed([text])[0]
    res = pine_db.query(vec, top_k=3, namespace=namespace)
    texts = retrieve_text_by_id([i["id"] for i in res["matches"] if i["score"] > 0.8])
    scores = [i["score"] for i in res["matches"]]
    similars = list(zip(texts, scores))
    return similars


def retrieve_text_by_id(ids: list):
    global local_db
    return [local_db[i] for i in ids]
