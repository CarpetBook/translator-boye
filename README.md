# translator boye

Discord bot powered by discord.py.

Thought to be just a translator, but now it's a testing ground for whatever god forsaken code I decide to throw at it.

so now, it can do:

- chatgpt
- transcription/translation
- resnet image recognition
- tesseract ocr

**UPDATE since I last updated this readme:**  
he now has long term "memory" using embeddings and pinecone!! not only does this augment his consistency and memory, but it also allows me to lower the memory size considerably, which lowers the average token usage to a very sane average. (which saves me MONEY)

**UPDATE UPDATE since I last updated this readme:**  
long term memory is disabled while I figure out how to make it more natural  
(but vectors are still being gathered and stored in pinecone)

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

### /shutdown \<password>

shuts down the bot. requires the randomly generated password. using the slash command with no password will print the current password in the console.

### /temperature \<number>

set the temperature of chatgpt's responses. higher temperature leads to more random, less stable responses. default is 0.75. temperature of 0 will always return the same response for a given chat history.

### **[NEW]** /undo

undoes the last message sent by chatgpt. removes both the last chatgpt message and the last user message from the chat memory.

### **[NEW]** /retry

regenerates the last response from chatgpt. if temperature is zero, this will have no effect, because the response will be exactly the same every time.

### **[NEW]** /edit \<new message>

change the last response from chatgpt.

### **[NEW]** /stop

if chatgpt is streaming a response, it will stop as soon as possible.

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
