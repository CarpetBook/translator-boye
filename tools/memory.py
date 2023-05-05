# ChatMemory class that manages the chat history in a single channel
from tools import vectors


class ChatMemory:
    def __init__(self, min_message_limit=5, max_message_limit=20):
        self.memory = []
        self.system = None
        self.starter = None
        self.min_message_limit = min_message_limit
        self.max_message_limit = max_message_limit
        self.role = "assistant"
        self.last_message = None

    def add(self, role, *message):
        for i in message:
            self.memory.append({"role": role, "content": i})
        self.clean()
        return self

    def construct(self, list=False):
        msgs = []
        for i in self.memory:
            msgs.append(i[1])

        if not list:
            return "\n".join(msgs)

        return msgs

    def clean(self):
        while len(self.memory) > self.max_message_limit:  # if the prompt is too long, cut off the oldest message... keep a minimum amount of messages
            user = None
            assistant = None
            text = ""
            if self.memory[0]["role"] == "system":
                user = self.memory[1]["content"]
                assistant = self.memory[2]["content"]
                self.memory = self.memory[3:]
            elif self.memory[0]["role"] == "user":
                user = self.memory[0]["content"]
                assistant = self.memory[1]["content"]
                self.memory = self.memory[2:]
            elif self.memory[0]["role"] == "assistant":
                assistant = self.memory[0]["content"]
                self.memory = self.memory[1:]
            if user is not None:
                text = f"User: {user}\n"
            text += f"Assistant: {assistant}"
            vectors.save_longterm_text([text])
            # self.memory = self.memory[3:]  # if chat memory is longer than 20 messages, cut off the oldest two
            if self.system is not None:
                self.memory.insert(0, {"role": "system", "content": self.system})
            print(len(self.memory))
            # print(fullprom)


    def clear(self):
        savetexts = []
        while len(self.memory) >= 2:
            user = None
            assistant = None
            text = ""
            if self.memory[0]["role"] == "system":
                user = self.memory[1]["content"]
                assistant = self.memory[2]["content"]
                self.memory = self.memory[3:]
            elif self.memory[0]["role"] == "user":
                user = self.memory[0]["content"]
                assistant = self.memory[1]["content"]
                self.memory = self.memory[2:]
            elif self.memory[0]["role"] == "assistant":
                assistant = self.memory[0]["content"]
                self.memory = self.memory[1:]
            if user is not None:
                text = f"User: {user}"
            text += f"\nAssistant: {assistant}"
            savetexts.append(text)

        if len(savetexts) > 0:
            vectors.save_longterm_text(savetexts)

        self.memory = []
        if self.system is not None:
            self.add("system", self.system)
        if self.starter is not None:
            self.add("assistant", self.starter)
        return self

    def get(self):
        return list(self.memory)

    def setsystem(self, newprompt):
        self.system = newprompt
        return self

    def setstarter(self, newstarter):
        self.starter = newstarter
        return self

    def setLastMessage(self, message):
        self.last_message = message
        return self
