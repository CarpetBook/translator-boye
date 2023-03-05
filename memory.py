# Memory class that manages the chat history in a single channel
# messages are timestamped and stored in a list as tuples (timestamp, message)
import time
import text


class ChatMemory:
    def __init__(self, min_message_limit=15, max_tokens=1024):
        self.memory = []
        self.prompt = ""
        self.tokens = 0
        self.min_message_limit = min_message_limit
        self.max_tokens = max_tokens
        self.name = "AI"

    def add(self, *message):
        for i in message:
            self.memory.append((time.time(), i))
        self.count_tokens()
        self.clean()
        return self

    def changename(self, name):
        self.name = name
        return self

    def construct(self, list=False):
        msgs = []
        for i in self.memory:
            msgs.append(i[1])

        if not list:
            return "\n".join(msgs)

        return msgs

    def count_tokens(self):
        self.tokens = text.tokenize(self.construct())["count"]
        return self.tokens

    def clean(self):
        print(self.count_tokens())

        while (
            self.tokens >= self.max_tokens
            and not len(self.memory) < self.min_message_limit
        ):  # if the prompt is too long, cut off the oldest message... keep a minimum amount of messages
            preface = self.memory[0]
            self.memory = self.memory[
                2:
            ]  # if chat memory is longer than 20 messages, cut off the oldest two
            self.memory.insert(0, preface)
            print(self.count_tokens())
            # print(fullprom)

    def clear(self):
        self.memory = []
        self.tokens = 0
        return self

    def get(self):
        return self.memory

    def setprompt(self, newprompt):
        self.prompt = newprompt
        return self


# class Memory:
#     def __init__(self):
#         self.memory = []

#     def add(self, user, *content):
#         for i in content:
#             self.memory.append((time.time(), user, i))
#             print("added to memory: " + str((time.time(), user, i)))
#             print(self.memory)
#         return self

#     def pop(self):
#         return self.memory.pop()

#     def clear(self):
#         self.memory = []
#         return self
