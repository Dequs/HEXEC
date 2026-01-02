import requests
import json
from google import generativeai
from datetime import datetime
from utils.functions import textToUUID, uuidToText


class AI:
    def __init__(self, api_key, model, api_key_comment=None, historyDir=None, chat: str = None):
        self.api_key = api_key
        if api_key_comment is None:
            self.api_key_comment = api_key
        else:
            self.api_key_comment = api_key_comment
        self.model = model
        self.prompt = ""

        if chat is not None:
            self.chat = chat
        else:
            self.chat = textToUUID(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        if historyDir is not None:
            self.historyDir = historyDir
        else:
            self.historyDir = "chats"


    def setHistoryDir(self, dir):
        self.historyDir = dir
        
    def setApiKey(self, api_key):
        self.api_key = api_key

    def getHistoryDir(self):
        return self.historyDir

    def setModel(self, model):
        self.model = model

    def setPrompt(self, dir):
        with open(dir, 'r') as file:
            self.prompt = file.read()

    def setChat(self, chatID):
        self.chat = chatID

    def getChat(self):
        return self.chat

    def send(self, userInput):
        if self.historyDir is not None:
            try:
                with open(f"{self.historyDir}/{self.chat}.elham", 'r') as file:
                    history = file.read()
            except FileNotFoundError:
                #print("History file not found, starting new history.")
                history = ""
                with open(f"{self.historyDir}/{self.chat}.elham", 'w') as file:
                    file.write("")
        generativeai.configure(api_key=self.api_key)
        modelInstance = generativeai.GenerativeModel(self.model)
        prompt = f"{history}\nUser input: {userInput}\n\n{self.prompt}"
        response = modelInstance.generate_content(prompt)
        if self.historyDir is not None:
            with open(f"{self.historyDir}/{self.chat}.elham", 'a') as file:
                file.write(f"User: {userInput}\nAI: {response.candidates[0].content.parts[0].text.strip()}\n")
        return response.candidates[0].content.parts[0].text.strip() if response.candidates else ""
    
    def comment(self, userInput): 
        generativeai.configure(api_key=self.api_key_comment)
        modelInstance = generativeai.GenerativeModel(self.model)
        prompt = open("promptComments.txt", 'r').read() # Sos, ciuchy i borciuchy
        response = modelInstance.generate_content(f"{prompt}\nUser input and AI response:\n{userInput}\n\nProvide a brief comment on the above interaction.")
        return response.candidates[0].content.parts[0].text.strip() if response.candidates else ""
    
    def formatResponse(self, response):
        import re
        # Remove markdown code block markers
        cleanResponse = response.strip()
        if cleanResponse.startswith("```json"):
            cleanResponse = cleanResponse[7:]
        elif cleanResponse.startswith("```"):
            cleanResponse = cleanResponse[3:]
        if cleanResponse.endswith("```"):
            cleanResponse = cleanResponse[:-3]
        cleanResponse = cleanResponse.strip()
        
        try:
            return json.loads(cleanResponse)
        except json.JSONDecodeError as e:
            # Try to fix common escaping issues with backslashes at line endings
            # Replace '\\' followed by newline with just '\\'
            cleanResponse = re.sub(r'\\\s*\n\s*', '', cleanResponse)
            try:
                return json.loads(cleanResponse)
            except json.JSONDecodeError:
                # If still failing, try to escape newlines within string values
                def escape_newlines_in_strings(match):
                    content = match.group(0)
                    # Replace actual newlines with escaped newlines (but keep already escaped ones)
                    content = content.replace('\n', '\\n').replace('\r', '\\r')
                    return content
                
                cleanResponse = re.sub(r'"(?:[^"\\]|\\.)*"', escape_newlines_in_strings, cleanResponse)
                try:
                    return json.loads(cleanResponse)
                except json.JSONDecodeError:
                    return None
        
