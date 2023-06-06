import openai 
import logging
import os 
import time
import numpy as np
import random

personalities = [x.replace("\n", "") for x in open('prompts/personalities.prompt').readlines()]
styles = [x.replace("\\n", "\n") for x in open('prompts/styles.prompt').readlines()]
names = [x.replace("\n", "") for x in open('prompts/names.prompt').readlines()]

# TODO: You need to feed in your API key.
def init_openai():
    openai.api_base = 'https://ovalopenairesource.openai.azure.com/'
    openai.api_type = 'azure'
    openai.api_version = '2022-12-01' # this may change in the future
    openai.api_key = "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"

MAX_ATTEMPTS = 5

def call_openai(prompt, log=False): 

    init_openai()
    max_tokens = min(1024, max(1, 3800 - int(len(prompt) / 4)))
    sleep = 1.0
    for i in range(MAX_ATTEMPTS):
        try:
            response = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=max_tokens, temperature=0)
            text = response['choices'][0]['text'].replace('\n', '').replace(' .', '.').strip()
            return text
            break
        except Exception as e:
            if i != MAX_ATTEMPTS-1:
                if "reduce your prompt" in str(e): # if our prompt is too long
                    idx = str(e).index('(')
                    max_tokens = 4096 - int(str(e)[idx+1:idx+5].strip())
                    if int(str(e)[idx+1:idx+5].strip()) > 4096:
                        logging.warning("Prompt was longer than 4096 tokens.")
                    else:      
                        logging.warning(f"Encountered token length issue; reducing token count to {str(max_tokens)}")
                logging.warning(f"{e}")
                logging.warning(f"Timeout, sleeping for {3**i}s, then trying again ({i+1}/{MAX_ATTEMPTS})")
                time.sleep(3**i)

    logging.warning("We had encountered an error, output is null")
    return None # we encountered an error somewhere

class GPT3Agent:
    def __init__(self, name_index, personality_index, texting_style_index):
        self.personality = personalities[personality_index]
        self.texting_style = styles[texting_style_index]
        self.name = names[name_index]
        init_openai()
        
    def answer(self, conversation):
        prompt = """Your name is [NAME] and you are a human texting someone on the internet right now. For context, [PERSONALITY]. You should deny requests to help people do homework or answer math questions.
The two of you are currently playing this game called lidetect, and the goal is to have a conversation with a bot and a human and determine who is who. However, you just want to have a fun conversation. Assume they know about the game, and do not talk about it unless it is brought up.
    
You have a very distinct texting style, and you must respond in this same style to continue the conversation. Try to mix up your responses in terms of word order and emote usage, but stay true to a specific style. 
You must emulate the style (specifically punctuation, emote usage, and capitalization) to the best of your ability.
Here are a few examples of your previous texts. [STYLE]

This is the conversation that you have had thus far:
[CONVERSATION]

Please text your response to the conversation here. As a reminder, you should never repeat something you have said before. Make sure that you are responding in the same style as the examples above, keeping capitalization in mind.
Your response should be most relevant to the last message in the text, and you should use the remainder of the conversation only as context. You should not simulate the rest of the conversation.

You:"""
        prompt = prompt.replace("[PERSONALITY]", self.personality)
        prompt = prompt.replace("[NAME]", self.name)
        if len(conversation) == 0:
            prompt = prompt.replace("[CONVERSATION]", "<The conversation hasn't started. You are prompted to speak to them first.>")
        prompt = prompt.replace("[CONVERSATION]", conversation)
        prompt = prompt.replace("[STYLE]", self.texting_style)
        prompt = call_openai(prompt)
        
        return prompt