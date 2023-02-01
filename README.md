# Image Slut

Discord bot powered by discord.py.

This bot will listen to certain configured channels and respond to messages like a standard chatbot. In the development server, these are the #image-slut-chat-1, #image-slut-chat-2, and #mark-chat-1 channels.

## Commands:

### !image \<prompt>
Generates a 512x512 image from the DALL-E 2 API.

### !redo
Generates another image from the last prompt.

### !variation
Generates a variation of the attached image using the DALL-E 2 API.

### !text \<prompt>
Completes the prompted text using the GPT-3 API.

### !clear
Clears the memory of the current chat channel. This command can't be used in a non-chat channel.

### !prompt
Shows the prompt used in the current chat channel. This command can't be used in a non-chat channel.

### !history
Shows the history of the messages sent in the current chat channel, along with some info about the current amount of tokens stored in memory and API cost of the prompt.

### !price \<text>
Calculates the price of a piece of text using the price of the Davinci model on the GPT-3 API.

### !ids \<text>
Calculates and shows the tokenized IDs of a piece of text using the GPT-2/3 tokenizer.

### !maxtoken \<number>
Sets the maximum number of tokens stored in memory for the current chat channel. Must be between 200 and 4000. This command can't be used in a non-chat channel.
