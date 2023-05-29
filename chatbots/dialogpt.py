from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import logging

MAX_LENGTH = 1000

#AI CHATBOT INFORMATION
# def get_chat_response(msg_text):
#     # Let's chat for x lines
#     # encode the new user input, add the eos_token and return a tensor in Pytorch
#     new_user_input_ids = tokenizer.encode(str(msg_text) + tokenizer.eos_token, return_tensors='pt')

#     # append the new user input tokens to the chat history
#     bot_input_ids = torch.cat([session["chat_history"], new_user_input_ids], dim=-1) if session.get("step") > 0 else new_user_input_ids

#     # generated a response while limiting the total chat history to 1000 tokens, 
#     chat_history_ids = model.generate(bot_input_ids, max_length=1000, pad_token_id=tokenizer.eos_token_id)

#     # pretty print last ouput tokens from bot
#     output = "DialoGPT: {}".format(tokenizer.decode(chat_history_ids[:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True))
#     session["step"] = session["step"] + 1
#     session["chat_history"] = chat_history_ids
#     return output

class DialoGPTAgent:
    def __init__(self, model_name='microsoft/DialoGPT-medium'):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        
    def answer(self, conversation):
        # my understanding is that the input to DialoGPT should be in the form of "user<eos>bot<eos>user<eos>"
        conversation = str(conversation).strip().replace('\nYou: ', self.tokenizer.eos_token).replace('\nUser: ', self.tokenizer.eos_token)
        prompt = conversation[1:] + self.tokenizer.eos_token
        print(prompt)
        input_ids = self.tokenizer.encode(prompt, return_tensors='pt')
        response = self.model.generate(input_ids, max_length=MAX_LENGTH, pad_token_id=self.tokenizer.eos_token_id)

        output = self.tokenizer.decode(response[:, input_ids.size(-1):][0], skip_special_tokens=True)
        return output