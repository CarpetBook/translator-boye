from PIL import Image
import pytesseract as pyt

REQUIRED_CONFIDENCE = 60


def run_ocr(file):
    filename = file.split("/")[-1]
    res = pyt.image_to_data(Image.open(file), output_type=pyt.Output.DICT)

    text = ""
    for i in range(len(res["text"])):
        if res["conf"][i] > REQUIRED_CONFIDENCE:
            text += res["text"][i] + " "

    # capital I fix, bc it shows as vertical line
    text = text.replace("|", "I")

    if len(text.strip()) == 0:
        text = "[OCR found no text]"
    if len(text.strip()) > 1900:
        trunc = text[:1900] + "\n[truncated due to Discord character limit]"
        with open(f"ocr/{filename}.txt", "w") as f:
            f.write(text)
        return ("file", trunc, f"ocr/{filename}.txt")
    return ("text", text)
