# ChatMemory class that manages the chat history in a single channel

class ChatMemory:
    def __init__(self, min_message_limit=15, max_message_limit=40):
        self.memory = []
        self.system = None
        self.starter = None
        self.min_message_limit = min_message_limit
        self.max_message_limit = max_message_limit
        self.role = "assistant"

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
            self.memory = self.memory[
                2:
            ]  # if chat memory is longer than 20 messages, cut off the oldest two
            self.memory.insert(0, {"role": "system", "content": self.system})
            print(len(self.memory))
            # print(fullprom)

    def clear(self):
        self.memory = []
        if self.system is not None:
            self.add("system", self.system)
        if self.starter is not None:
            self.add("assistant", self.starter)
        return self

    def get(self):
        return self.memory

    def setsystem(self, newprompt):
        self.system = newprompt
        return self

    def setstarter(self, newstarter):
        self.starter = newstarter
        return self
