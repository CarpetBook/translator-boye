from PIL import Image
import pytesseract as pyt

REQUIRED_CONFIDENCE = 60


def run_ocr(file):
    res = pyt.image_to_data(Image.open(file), output_type=pyt.Output.DICT)

    text = ""
    for i in range(len(res["text"])):
        if res["conf"][i] > REQUIRED_CONFIDENCE:
            text += res["text"][i] + " "

    return text
