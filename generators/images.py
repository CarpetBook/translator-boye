import base64
import openai
import os
import time
import requests
from PIL import Image, ImageDraw


async def genpic(genprompt: str):
    try:
        tic = time.time()
        res = openai.Image.create(
            prompt=genprompt, n=1, size="512x512", response_format="b64_json"
        )
        toc = time.time()

        timer = str(round(toc - tic, 2))

        filename = "./imageslut_pics/" + str(time.time()) + " res.png"

        img_data = res["data"][0]["b64_json"]
        with open(filename, "wb") as fh:
            fh.write(base64.b64decode(img_data))

        return ("success", filename, timer)

    except openai.error.OpenAIError as e:
        return ("fail", e)


async def downloadpic(url: str):
    img_data = requests.get(url).content
    filename = "./edit_pics/" + str(time.time()) + ".png"
    with open(filename, "wb") as handler:
        handler.write(img_data)

    return filename


async def editpic(filename: str, genprompt: str):
    image = Image.open(filename)

    image = cropSquare(image)
    mask = makeTransparentEllipse(image)

    maskfile = filename + " mask.png"
    oldfile = filename + " before.png"
    image.save(oldfile)
    mask.save(maskfile)

    try:
        tic = time.time()
        res = openai.Image.create_edit(
            image=open(oldfile, "rb"),
            mask=open(maskfile, "rb"),
            prompt=genprompt,
            n=1,
            size="512x512",
            response_format="b64_json",
        )
        toc = time.time()

        timer = str(round(toc - tic, 2))

        newfile = "./edit_pics/" + str(time.time()) + " after.png"

        img_data = res["data"][0]["b64_json"]
        with open(newfile, "wb") as fh:
            fh.write(base64.b64decode(img_data))

        return ("success", newfile, timer)
    except openai.error.OpenAIError as e:
        return ("fail", e)


async def variationpic(filename: str):
    image = Image.open(filename)

    image = cropSquare(image)

    oldfile = filename + " before.png"
    image.save(oldfile)

    try:
        tic = time.time()
        res = openai.Image.create_variation(
            image=open(oldfile, "rb"), n=1, size="512x512", response_format="b64_json"
        )
        toc = time.time()

        timer = str(round(toc - tic, 2))

        newfile = "./edit_pics/" + str(time.time()) + " after.png"

        img_data = res["data"][0]["b64_json"]
        with open(newfile, "wb") as fh:
            fh.write(base64.b64decode(img_data))

        return ("success", newfile, timer)
    except openai.error.OpenAIError as e:
        return ("fail", e)


def cropSquare(image: Image):
    width, height = image.size
    if width == height:
        return image
    elif width > height:
        diff = width - height
        left = diff / 2
        right = width - left
        top = 0
        bottom = height
        image = image.crop((left, top, right, bottom))
    else:
        diff = height - width
        left = 0
        right = width
        top = diff / 2
        bottom = height - top
        image = image.crop((left, top, right, bottom))

    # verify if image is square
    width, height = image.size
    if abs(width - height) == 1:
        if width > height:
            return image.crop((0, 0, height, height))
        else:
            return image.crop((0, 0, width, width))


def makeTransparentEllipse(image: Image):
    width, height = image.size
    mask = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, width, height), fill=(0, 0, 0, 0))
    # return draw as Image
    return mask
