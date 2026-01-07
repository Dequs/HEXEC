import requests
import json
from google import generativeai
from datetime import datetime
from utils.functions import textToUUID, uuidToText
import logging
import time
from utils.commands import Colors, CommandExecutor

logging.basicConfig(
    level=logging.INFO,
    filename="logs.log",
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

class AI:
    def __init__(self, api_key=None, model=None, api_key_comment=None, historyDir=None, chat: str = None, **kwargs):
        logger.info("Initializing AI client.")
        # accept both naming styles for backward compatibility
        self.apiKey = api_key or kwargs.get('apiKey') or kwargs.get('apiKeyComment') or api_key
        if api_key_comment is None:
            logger.info("No comment API key provided, using main API key for comments.")
            self.apiKeyComment = self.apiKey
        else:
            self.apiKeyComment = api_key_comment
        self.model = model or kwargs.get('model')
        self.prompt = ""
        self.dryRun = False

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
        
    def setApiKey(self, apiKey):
        logger.info("Setting new API key.")
        self.apiKey = apiKey

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

    def setDryRun(self, dryRun: bool):
        logger.info(f"Setting dry run mode to: {dryRun}")
        self.dryRun = dryRun

    def getDryRun(self) -> bool:
        logger.info(f"Getting dry run mode: {self.dryRun}")
        return self.dryRun

    def _executeImmediateCommand(self, commandData):
        logger.info(f"Executing immediate command: {commandData.get('command', '')}")
        
        if self.dryRun:
            return "Dry run - command not executed."
        
        executor = CommandExecutor(dryRun=False, safeMode=False, explain=False)
        result, success = executor.execute(commandData)
        
        if success:
            return f"Success: {result[:500]}"
        else:
            return f"Error: {result[:500]}"
        
    def executeImmediateCommand(self, commandData):
        if self.dryRun:
            return "Dry run - command not executed."
        
        executor = CommandExecutor(dryRun=False, safeMode=False, explain=True)
        result, success = executor.execute(commandData)
        
        if success:
            return result
        else:
            return f"Error: {result[:200]}"

    def _sendStream(self, userInput, response, immediateExecution=False):
        fullResponse = ""
        currentResult = ""
        jsonBuffer = ""
        inJson = False
        jsonDepth = 0
        
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
                    ch = textChunk[i]
                    if ch == '{':
                        if not inJson:
                            inJson = True
                            jsonBuffer = ''
                            jsonDepth = 0
                        jsonDepth += 1
                        jsonBuffer += ch
                    elif ch == '}':
                        jsonBuffer += ch
                        jsonDepth -= 1
                        if inJson and jsonDepth == 0:
                            inJson = False
                            try:
                                commandData = json.loads(jsonBuffer)
                                if immediateExecution and commandData.get('execute_immediately', False):
                                    result = self._executeImmediateCommand(commandData)
                                    currentResult = f"\n[IMMEDIATE RESULT]: {result}\n"
                                    yield currentResult
                                    jsonBuffer = ''
                            except Exception:
                                pass
                    elif inJson:
                        jsonBuffer += ch
                    time.sleep(0.002)
                    yield ch + (currentResult if (i == len(textChunk)-1 and currentResult) else '')
                    i += 1
        
        if self.historyDir is not None:
            with open(f"{self.historyDir}/{self.chat}.elham", 'a') as file:
                file.write(f"User: {userInput}\nAI: {fullResponse.strip()}\nResult: {currentResult}\n")

    class EnhancedHistory:
        def __init__(self, history_dir, chat_id):
            self.history_dir = history_dir
            self.chat_id = chat_id
            self.context = []
        def addInteraction(self, user_input, ai_response, result=None):
            timestamp = datetime.now().isoformat()
            entry = {
                'timestamp': timestamp,
                'user': user_input,
                'ai': ai_response,
                'result': result,
                'context': self.context.copy()
            }
            with open(f"{self.history_dir}/{self.chat_id}.jsonl", 'a') as f:
                f.write(json.dumps(entry) + '\n')
            self.context.append(entry)
            if len(self.context) > 10:
                self.context.pop(0)
        def getContextSummary(self):
            summary = []
            for entry in self.context[-3:]:
                if entry.get('result'):
                    summary.append(f"Result: {str(entry['result'])[:100]}...")
            return "\n".join(summary)

    def send(self, userInput, stream=False, immediateExecution=False):
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
        generativeai.configure(api_key=self.apiKey)
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
            return self._sendStream(userInput, response, immediateExecution)
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
        generativeai.configure(api_key=self.apiKeyComment)
        modelInstance = generativeai.GenerativeModel(self.model)
        prompt = open("promptComments.txt", 'r').read()
        logger.info("Generating comment content from AI model.")
        response = modelInstance.generate_content(f"{prompt}\nUser input and AI response:\n{userInput}\n\nProvide a brief comment on the above interaction.")
        logger.info("Comment generated successfully.")
        return response.candidates[0].content.parts[0].text.strip() if response.candidates else ""
    
    def formatResponse(self, response):
        import re
        if not isinstance(response, str):
            try:
                response = str(response)
            except:
                return None

        cleanResponse = re.sub(r'\x1b\[[0-9;]*m', '', response)
        cleanResponse = cleanResponse.strip()

        if cleanResponse.startswith("```json"):
            cleanResponse = cleanResponse[7:]
        elif cleanResponse.startswith("```"):
            cleanResponse = cleanResponse[3:]
        if cleanResponse.endswith("```"):
            cleanResponse = cleanResponse[:-3]
        cleanResponse = cleanResponse.strip()

        try:
            return json.loads(cleanResponse)
        except json.JSONDecodeError:
            pass

        starts = [m.start() for m in re.finditer(r"\{", cleanResponse)]
        for start in starts:
            depth = 0
            for i in range(start, len(cleanResponse)):
                ch = cleanResponse[i]
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        candidate = cleanResponse[start:i+1]
                        try:
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            break

        clean2 = re.sub(r'\\\s*\n\s*', '', cleanResponse)
        try:
            return json.loads(clean2)
        except json.JSONDecodeError:
            def escapeNewlinesInStrings(match):
                content = match.group(0)
                content = content.replace('\n', '\\n').replace('\r', '\\r')
                return content
            clean3 = re.sub(r'"(?:[^"\\]|\\.)*"', escapeNewlinesInStrings, clean2)
            try:
                return json.loads(clean3)
            except json.JSONDecodeError:
                return None

    def processStepByStep(self, initialInput, maxSteps=10):
        logger.info("Starting step-by-step processing")
        steps = []
        currentInput = initialInput
        
        for step in range(maxSteps):
            print(f"{Colors.OKCYAN}[Step {step+1}/{maxSteps}]{Colors.ENDC}")
            
            responseText = ""
            print(f"{Colors.GREY}AI is generating response...{Colors.ENDC}")
            
            for chunk in self.send(currentInput, stream=True, immediateExecution=True):
                print(chunk, end='', flush=True)
                responseText += chunk
            
            print(f"\n{Colors.DIVIDER}")
            
            try:
                responseData = self.formatResponse(responseText)
                if responseData and "done" in responseData and responseData["done"]:
                    print(f"{Colors.OKGREEN}Task completed!{Colors.ENDC}")
                    break
            except:
                pass
            
            steps.append({
                "input": currentInput,
                "response": responseText[:500]
            })
            
            if step == maxSteps - 1:
                print(f"{Colors.WARNING}Maximum steps reached.{Colors.ENDC}")
                break
            
            nextAction = input(f"{Colors.OKCYAN}Enter next instruction or 'done': {Colors.ENDC}")
            if nextAction.lower() == 'done':
                print(f"{Colors.OKGREEN}Task marked as completed by user.{Colors.ENDC}")
                break
            
            currentInput = f"Previous step result: {responseText[:500]}\nNext instruction: {nextAction}"

class InteractiveExecutor:
    def __init__(self, aiClient, streamMode=True):
        self.aiClient = aiClient
        self.streamMode = streamMode
        self.commandHistory = []
        
    def executeWithFeedback(self, userInput):
        print(f"{Colors.OKCYAN}Starting interactive execution...{Colors.ENDC}")
        
        while True:
            response = self.aiClient.send(userInput, stream=self.streamMode)
            
            commandData = self.aiClient.formatResponse(response)
            if not commandData or "commands" not in commandData:
                return "No valid command received"

            for cmd in commandData["commands"]:
                executor = CommandExecutor()
                result, success = executor.execute(cmd)
                
                self.commandHistory.append({
                    "command": cmd["command"],
                    "result": result,
                    "success": success
                })
                
                if self.streamMode:
                    print(f"\n{Colors.OKGREEN}Command executed{Colors.ENDC}")
                    print(f"{Colors.GREY}Result: {result[:200]}...{Colors.ENDC}")
                
                if not success and not cmd.get("continue_on_error", False):
                    return f"Command failed: {result}"
            
            userInput = "Previous command executed. Provide next command or say 'complete' if finished."

class AiFlowProcessor:
    def __init__(self, aiClient, executor):
        self.aiClient = aiClient
        self.executor = executor
        self.state = "idle"
        self.results = []
        
    def processRequest(self, userInput):
        self.state = "processing"
        
        while self.state != "complete":
            aiResponse = self.aiClient.send(userInput, stream=True)
            
            for chunk in aiResponse:
                if self.containsImmediateCommand(chunk):
                    command = self.extractCommand(chunk)
                    result = self.executor.execute(command)
                    
                    self.results.append(result)
                    
                    if command.get("wait_for_result"):
                        userInput = f"Previous result: {result}. What's next?"
                    else:
                        continue
            
            if self.isCompletionSignal(aiResponse):
                self.state = "complete"
        
        return self.results
    
    def containsImmediateCommand(self, text):
        return "execute_immediately" in text.lower()
    
    def extractCommand(self, text):
        try:
            return json.loads(text)
        except:
            return {}
    
    def isCompletionSignal(self, response):
        responseText = str(response)
        return "complete" in responseText.lower() or "done" in responseText.lower()