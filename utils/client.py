import requests
import json
from google import generativeai
from datetime import datetime
from utils.functions import textToUUID, uuidToText
import logging
import time
from utils.commands import Colors

logging.basicConfig(
    level=logging.INFO,
    filename="logs.log",
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

class AI:
    def __init__(self, api_key, model, api_key_comment=None, historyDir=None, chat: str = None):
        logger.info("Initializing AI client.")
        self.api_key = api_key
        if api_key_comment is None:
            logger.info("No comment API key provided, using main API key for comments.")
            self.api_key_comment = api_key
        else:
            self.api_key_comment = api_key_comment
        self.model = model
        self.prompt = ""

        if chat is not None:
            logger.info("Chat ID provided.")
            self.chat = chat
        else:
            logger.info("No Chat ID provided, generating new one.")
            self.chat = textToUUID(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        if historyDir is not None:
            self.historyDir = historyDir
        else:
            self.historyDir = "chats"


    def setHistoryDir(self, dir):
        logger.info(f"Setting history directory to: {dir}")
        self.historyDir = dir
        
    def setApiKey(self, api_key):
        logger.info("Setting new API key.")
        self.api_key = api_key

    def getHistoryDir(self):
        logger.info(f"Getting history directory: {self.historyDir}")
        return self.historyDir

    def setModel(self, model):
        logger.info(f"Setting model to: {model}")
        self.model = model

    def setPrompt(self, dir):
        logger.info(f"Setting prompt from file: {dir}")
        with open(dir, 'r') as file:
            self.prompt = file.read()

    def setChat(self, chatID):
        logger.info(f"Setting chat ID to: {chatID}")
        self.chat = chatID

    def getChat(self):
        logger.info(f"Getting chat ID: {self.chat}")
        return self.chat
    
    def getChatDir(self):
        logger.info(f"Getting chat directory: {self.historyDir}")
        return self.historyDir

    def _sendStream(self, userInput, response):
        fullResponse = ""
        for chunk in response:
            if chunk.candidates and chunk.candidates[0].content.parts:
                textChunk = chunk.candidates[0].content.parts[0].text
                fullResponse += textChunk
                i = 0
                bold = False
                while i < len(textChunk):
                    if textChunk[i:i+2] == "**":
                        bold = not bold
                        yield Colors.ENDC if bold else Colors.GREY
                        i += 2
                        continue
                    time.sleep(2 / 1000)
                    yield textChunk[i]
                    i += 1
        
        if self.historyDir is not None:
            logger.info("Appending interaction to chat history.")
            with open(f"{self.historyDir}/{self.chat}.elham", 'a') as file:
                file.write(f"User: {userInput}\nAI: {fullResponse.strip()}\n")
        logger.info("Interaction appended to history successfully.")

    def send(self, userInput, stream=False):
        if self.historyDir is not None:
            logger.info("Loading chat history...")
            try:
                with open(f"{self.historyDir}/{self.chat}.elham", 'r') as file:
                    history = file.read()
                with open(f"{self.historyDir}/{self.chat}.json", 'r') as indexFile:
                    settings = json.loads(indexFile.read())
                logger.info("Chat history loaded successfully.")
            except FileNotFoundError:
                logger.warning("History file not found, starting new history.")
                history = ""
                with open(f"{self.historyDir}/{self.chat}.elham", 'w') as file:
                    file.write("")
                with open(f"{self.historyDir}/{self.chat}.json", 'a') as indexFile:
                    settings = {
                        "custom_name": None,
                        "model": self.model,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "custom_prompt": None
                    }
                    indexFile.write(json.dumps(settings) + "\n")
        logger.info("Sending user input to AI model.")
        generativeai.configure(api_key=self.api_key)
        self.model = settings.get("model", self.model)
        modelInstance = generativeai.GenerativeModel(self.model)
        logger.info(f"Using model: {self.model}")
        if settings["custom_prompt"] is not None:
            logger.info("Using custom prompt from settings.")
            prompt = f"{history}\nUser input: {userInput}\n\n{settings['custom_prompt']}"
        else:
            logger.info("Using default prompt.")
            prompt = f"{history}\nUser input: {userInput}\n\n{self.prompt}"
        logger.info("Generating content from AI model.")
        response = modelInstance.generate_content(prompt, stream=stream)
        logger.info("Content generated successfully.")
        
        if stream:
            logger.info("Streaming response enabled.")
            return self._sendStream(userInput, response)
        else:
            fullResponse = response.candidates[0].content.parts[0].text.strip() if response.candidates else ""
            
            if self.historyDir is not None:
                logger.info("Appending interaction to chat history.")
                with open(f"{self.historyDir}/{self.chat}.elham", 'a') as file:
                    file.write(f"User: {userInput}\nAI: {fullResponse.strip()}\n")
            logger.info("Interaction appended to history successfully.")
            return fullResponse
    
    def comment(self, userInput): 
        logger.info("Generating comment for user input.")
        generativeai.configure(api_key=self.api_key_comment)
        modelInstance = generativeai.GenerativeModel(self.model)
        prompt = open("promptComments.txt", 'r').read() # Sos, ciuchy i borciuchy
        logger.info("Generating comment content from AI model.")
        response = modelInstance.generate_content(f"{prompt}\nUser input and AI response:\n{userInput}\n\nProvide a brief comment on the above interaction.")
        logger.info("Comment generated successfully.")
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
