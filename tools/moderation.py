import openai
import tenacity


@tenacity.retry(stop=tenacity.stop_after_attempt(3))
def classify(text):
    response = openai.Moderation.create(
        input=text
    )

    print(response["results"][0])

    restext = ""
    res = response["results"][0]
    flagged_reasons = [r[0].title() for r in res["categories"].items() if r[1] is True]
    flagged_reasons_str = ", ".join(flagged_reasons)

    if res["flagged"]:
        restext = "This message would have been flagged by OpenAI's moderation API.\n"
        restext += f"Reason(s): {flagged_reasons_str}\n\n"
    else:
        restext = "This message would not have been flagged by OpenAI's moderation API.\n\n"

    # sort category_scores dict by value
    top_categories = sorted(res["category_scores"].items(), key=lambda x: x[1], reverse=True)
    strs = []
    for cat, score in top_categories:
        if score < 0.0001:
            continue
        cat = cat.title()
        score = "{:.2f}".format(score * 100)
        strs.append(f"{cat}: {score}%")

    if len(strs) >= 1:
        restext += "Likelihood of flagged content:\n"
        restext += "\n".join(strs)

    return ("success", restext)
