import json

def addTokens(tokens: tuple, user: tuple):
    # expecting tokens to be a tuple of (prompt, completion)
    # expecting user to be a tuple of (name, id)

    # open tokens.json file
    with open("tokens.json", "r") as f:
        data = json.load(f)
        # add tokens to data
        