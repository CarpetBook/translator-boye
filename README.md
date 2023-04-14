# translator boye

Discord bot powered by discord.py.

Thought to be just a translator, but now it's a testing ground for whatever god forsaken code I decide to throw at it.

so now, it can do:

- chatgpt
- transcription
- resnet image recognition
- tesseract ocr

**UPDATE since I last updated this readme:**  
he now has long term "memory" using embeddings and pinecone!! not only does this augment his consistency and memory, but it also allows me to lower the memory size considerably, which lowers the average token usage to a very sane average. (which saves me MONEY)

## Commands

### /setchat

establishes the current channel as a chat channel.

### /unchat

removes the current channel as a chat channel.

### /clear

clears the chat memory.

### /system-prompt \<message> [clear?]

sets the system prompt for chatgpt. set [clear?] to false if you don't want to clear the chat memory along with the new prompt. chatgpt doesn't listen strongly to system messages, so using a starter message as an example is advised.

### /starter-message \<message> [clear?]

sets the starter message for chatgpt. set [clear?] to false if you don't want to clear the chat memory along with the new prompt. this places a message right after the system prompt, and marks it as if chatgpt said it first.

### /setprefix \<prefix>

sets the prefix that you have to use to send a message to chatgpt. defaults to none, so messages that are sent in the channel go straight to chatgpt. if you set a prefix and you want to remove it, do /setprefix none.

### /startwith \<string>

prepends a string to chatgpt's messages before it replies. this was a sketchy test thing that never ended up being used, bc it was meant to chat with other bots (by using their prefix on its messages).

### !translate [link]

transcribes and translates the audio file, video file, or link attached to your message.

### !transcribe [link]

just transcribes the audio file, video file, or link attached to your message.

### !summarize [link]

transcribes an audio/video file or link with the "base" model in whisper for speed, then sends the chunked transcript to chatgpt to be summarized. works better with short-form content. chunking allows it to work on longer content at the cost of summary quality.

### !ocr

uses tesseract to try and read the text in the attached image. if the text is too long, it sends the entire text as a file.

### !resnet

runs resnet-152 on the attached image and returns the top 5 results.

### !moderation \<message>

sends the message to the openAI's moderation API to be checked. returns a percentage likelihood of the message being flagged for different reasons, and determines whether or not the message would be flagged [true/false].
