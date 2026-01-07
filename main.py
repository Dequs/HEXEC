from utils.functions import Installation
from utils.config import Config
config = Config()
if config.loadConfig() == {}:
    installation = Installation()
    if installation.needsInstallation():
        print("Installing missing dependencies...")
        installation.performInstallation()
        print("Installation complete. Please restart the application.")
        exit()

from utils.client import AI
from colorama import Fore
from utils.commands import CommandExecutor
from utils.functions import uuidToText, Update, ask, changeConsoleTitle
import contextlib
import io
import os
import time
import shutil
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
import json

os.system("cls")

changeConsoleTitle("HEXEC by Dequs")

class Colors:
    HEADER = Fore.LIGHTBLUE_EX
    OKBLUE = Fore.BLUE
    OKCYAN = Fore.CYAN
    OKGREEN = Fore.GREEN
    WARNING = Fore.YELLOW
    GREY = Fore.LIGHTBLACK_EX
    FAIL = Fore.RED
    ENDC = Fore.RESET
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    DIVIDER = Fore.LIGHTBLACK_EX + "="*50 + Fore.RESET

# Please volvo fix your game

with open("VERSION", "r") as versionFile:
    currentVersion = versionFile.read().strip()

update = Update(currentVersion)
check = update.checkForUpdates()

changeConsoleTitle("Menu - HEXEC")
def menu():
    global config, choice, chats
    print(fr"""
        
    {Colors.HEADER}
    $$\   $$\ $$$$$$$$\ $$\   $$\ $$$$$$$$\  $$$$$$\  
    $$ |  $$ |$$  _____|$$ |  $$ |$$  _____|$$  __$$\ 
    $$ |  $$ |$$ |      \$$\ $$  |$$ |      $$ /  \__|
    $$$$$$$$ |$$$$$\     \$$$$  / $$$$$\    $$ |      
    $$  __$$ |$$  __|    $$  $$<  $$  __|   $$ |      
    $$ |  $$ |$$ |      $$  /\$$\ $$ |      $$ |  $$\ 
    $$ |  $$ |$$$$$$$$\ $$ /  $$ |$$$$$$$$\ \$$$$$$  |
    \__|  \__|\________|\__|  \__|\________| \______/ 
                                                    
        {update.display() if update.checkForUpdates() else f"Current version: {currentVersion} {Colors.OKGREEN}{"(up to date)" if not update.wrong else f"{Colors.FAIL}(corrupted or invalid)"}{Colors.ENDC}"}                                               
        Created by: {Fore.YELLOW}Dequs{Colors.ENDC}
    """)

    if update.update:
        print(f"\n{Colors.OKGREEN}A new update is available!{Colors.ENDC}\n")
        choice = input(f"\n{Colors.WARNING}Do you want to apply the update now? (y/n): {Colors.ENDC}").lower()
        if choice == 'y':
            print(f"\n{Colors.OKGREEN}Applying update...{Colors.ENDC}\n")
            if update.applyUpdate():
                print(f"{Colors.OKGREEN}Update applied successfully! Please restart the application.{Colors.ENDC}")
                exit()
            else:
                print(f"{Colors.FAIL}Failed to apply the update. Please try again later.{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}Update skipped. You can update later from the settings.{Colors.ENDC}")

    if config.loadConfig() == {}:
        api_key = input("Enter your API Key: ")
        apiKeyComment = input("Enter a comment for your API Key (optional): ")
        model = input("Enter the model to use (e.g., gemini-2.5-flash): ")
        ask = input("Always ask you before executing commands (y/n):").lower()
        settings = {
                "API_KEY": api_key,
                "API_KEY_COMMENT": apiKeyComment if apiKeyComment else api_key,
                "model": model,
                "alwaysAsk": True if ask == 'y' else False
            }
        config = Config()
        config.createConfig(settings)

    x = 1

    chats = {}

    print(f"\n{Colors.HEADER}{'='*50}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}Available Chats:{Colors.ENDC}\n")

    try:
        os.mkdir("chats")
    except FileExistsError:
        pass

    for file in os.listdir("chats"):
        if file.endswith(".elham"):
            with open(f"chats/{file.split('.elham')[0]}.json", 'r') as indexFile:
                settings = json.loads(indexFile.read())
                if settings.get("custom_name"):
                    print(f"  {Colors.OKBLUE}[{x}]{Colors.ENDC} {Colors.OKBLUE}{settings['custom_name']}{Colors.ENDC}")
                    print(f"      {Colors.OKCYAN}Created: {settings['created_at']}{Colors.ENDC}")
                    chats[x] = file
                    x += 1
                    continue
                else:
                    print(f"  {Colors.OKBLUE}[{x}]{Colors.ENDC} {Colors.OKBLUE}{file.split('.elham')[0]}{Colors.ENDC}")
                    print(f"      {Colors.OKCYAN}Created: {uuidToText(file.split('.elham')[0])}{Colors.ENDC}")
            chats[x] = file
            x += 1  

    print(f"\n  {Colors.OKGREEN}[{x}]{Colors.ENDC} {Colors.OKGREEN}Start new chat{Colors.ENDC}")
    if x+1 <= 2:
        pass
    else:
        print(f"  {Colors.FAIL}[{x+1}]{Colors.ENDC} {Colors.FAIL}Delete all chat histories{Colors.ENDC}")

    print(f"\n{Colors.HEADER}{'='*50}{Colors.ENDC}")
    autoCompletionChat = []
    for i in range(1, x+2):
        autoCompletionChat.append(f"{str(i)} rename")
        autoCompletionChat.append(f"{str(i)} delete")
        autoCompletionChat.append(f"{str(i)} info")
        autoCompletionChat.append(f"{str(i)} model")
    chatCompleter = WordCompleter(autoCompletionChat, ignore_case=True, sentence=True)
    session = PromptSession(completer=chatCompleter)
    rawChoice = session.prompt(ANSI(f"{Colors.OKCYAN}>>>: {Colors.ENDC} "))

    choice = rawChoice.split()

    try:
        if len(choice) > 1:
            idx = int(choice[0])
            action = choice[1].lower()
            if idx in chats:
                if action == "rename":
                    newName = input(f"{Colors.OKCYAN}Enter new name for chat '{chats[idx]}': {Colors.ENDC}")
                    with open(f"chats/{chats[idx].split('.elham')[0]}.json", 'r') as indexFile:
                        settings = json.loads(indexFile.read())
                    settings["custom_name"] = newName
                    with open(f"chats/{chats[idx].split('.elham')[0]}.json", 'w') as indexFile:
                        indexFile.write(json.dumps(settings) + "\n")
                    print(f"{Colors.OKGREEN}Chat renamed successfully to '{newName}'.{Colors.ENDC}\n")
                    os.system("cls")
                elif action == "delete":
                    os.remove(f"chats/{chats[idx]}")
                    os.remove(f"chats/{chats[idx].split('.elham')[0]}.json")
                    print(f"{Colors.OKGREEN}Chat '{chats[idx]}' deleted successfully.{Colors.ENDC}\n")
                    os.system("cls")
                elif action == "info":
                    with open(f"chats/{chats[idx].split('.elham')[0]}.json", 'r') as indexFile:
                        settings = json.loads(indexFile.read())
                    print(f"{Colors.OKGREEN}Chat Information for '{chats[idx]}':{Colors.ENDC}\n")
                    print(f"  {Colors.OKBLUE}Custom Name: {settings.get('custom_name', 'N/A')}{Colors.ENDC}")
                    print(f"  {Colors.OKBLUE}Model: {settings.get('model', 'N/A')}{Colors.ENDC}")
                    print(f"  {Colors.OKBLUE}Created At: {settings.get('created_at', 'N/A')}{Colors.ENDC}")
                    print(f"  {Colors.OKBLUE}Custom Prompt: {settings.get('custom_prompt', 'N/A')}{Colors.ENDC}\n")
                    input(f"{Colors.WARNING}Press Enter to continue...{Colors.ENDC}")
                    os.system("cls")
                elif action == "model":
                    with open(f"chats/{chats[idx].split('.elham')[0]}.json", 'r') as indexFile:
                        settings = json.loads(indexFile.read())
                time.sleep(1)
                menu()
            elif idx == x + 1:
                try:
                    for file in os.listdir("chats"):
                        os.remove(f"chats/{file}")
                    print(f"{Colors.OKGREEN}All chat histories deleted successfully.{Colors.ENDC} Restarting program...\n")
                    time.sleep(2)
                    menu()
                except FileNotFoundError:
                    print(f"{Colors.WARNING}No chat histories to delete.{Colors.ENDC}\n")
        else:
            idx = int(choice[0])
            if idx == x + 1:
                try:
                    for file in os.listdir("chats"):
                        os.remove(f"chats/{file}")
                    print(f"{Colors.OKGREEN}All chat histories deleted successfully.{Colors.ENDC} Restarting program...\n")
                    time.sleep(2)
                    menu()
                except FileNotFoundError:
                    print(f"{Colors.WARNING}No chat histories to delete.{Colors.ENDC}\n")
    except Exception:
        pass

    os.system("cls")
    if int(choice[0]) in chats:
        with open(f"chats/{chats[int(choice[0])]}", "r") as f:
            x = 0
            l = f.readlines()
            for line in l:
                if line.startswith("User: ") or line.startswith("AI: "):
                    x+=1

        termWidth = shutil.get_terminal_size().columns

        leftText = f"{Colors.OKGREEN}Selected chat: {chats[int(choice[0])] if int(choice[0]) in chats else 'New Chat'}{Colors.ENDC}"
        rightText = f"{Colors.OKCYAN}[Messages: {x}]{Colors.ENDC}"

        spaces = termWidth - len(rightText) - len(leftText) + 19
        if spaces < 1:
            spaces = 1

        print(leftText + " " * spaces + rightText)

    changeConsoleTitle(chats[int(choice[0])] if int(choice[0]) in chats else "New Chat")

menu()

config = Config()
apiKey = config.get("API_KEY")
model = config.get("model")
askMode = config.get("alwaysAsk")
apiKeyComment = config.get("API_KEY_COMMENT")

if askMode != True:
    print(f"{Colors.WARNING}[WARNING] askMode is disabled, please turn it on!{Colors.ENDC}\n")

aiClient = AI(api_key=apiKey, model=model, api_key_comment=apiKeyComment, chat=chats[int(choice[0])].split(".elham")[0] if int(choice[0]) in chats else None)
aiClient.setPrompt("prompt.txt")

aiClientThink = AI(api_key=apiKey, model=model, api_key_comment=apiKeyComment, chat=chats[int(choice[0])].split(".elham")[0] if int(choice[0]) in chats else None)
aiClientThink.setPrompt("promptThinking.txt")

while True:
    internalCommands = ["exit", "config", "cls", "clear", "history", "reset", "dryrun", "menu", "clearlogs"]
    commandCompleter = WordCompleter(internalCommands, ignore_case=True, sentence=True)
    session = PromptSession(completer=commandCompleter)
    userInput = session.prompt(ANSI(f"{Colors.OKCYAN}>>>{Colors.ENDC} "))
    if not userInput.strip():
        continue

    if userInput.split()[0].lower() in internalCommands:
        command = internalCommands.index(userInput.split()[0].lower())

        if command == 0:
            print(f"{Colors.OKGREEN}Exiting AI Control. Goodbye!{Colors.ENDC}")
            break
        elif command == 1:
            api_key = input("Enter your API Key: ")
            apiKeyComment = input("Enter a comment for your API Key (optional): ")
            model = input("Enter the model to use (e.g., gemini-2.5-flash): ")
            ask = input("Always ask you before executing commands (y/n):").lower()
            settings = {
                "API_KEY": api_key,
                "API_KEY_COMMENT": apiKeyComment if apiKeyComment else api_key,
                "model": model,
                "alwaysAsk": True if ask == 'y' else False
            }
            Config.createConfig(settings)
            print(f"{Colors.OKGREEN}Configuration updated successfully.{Colors.ENDC}")
            continue
        elif command == 2 or command == 3:
            import os
            os.system('cls' if os.name == 'nt' else 'clear')
            continue
        elif command == 4:
            import os
            try:
                for file in os.listdir("chats"):
                    os.remove(f"chats/{file}")
                print(f"{Colors.OKGREEN}History reset successfully.{Colors.ENDC}\n")
            except FileNotFoundError:
                print(f"{Colors.WARNING}No history to reset.{Colors.ENDC}\n")
            continue
        elif command == 6:
            if aiClient.getDryRun():
                aiClient.setDryRun(False)
                print(f"{Colors.OKGREEN}Dry run mode disabled. Commands will be executed normally.{Colors.ENDC}\n")
            else:
                aiClient.setDryRun(True)
                print(f"{Colors.OKGREEN}Dry run mode enabled. Commands will not be executed.{Colors.ENDC}\n")
            continue
        elif command == 7:
            os.system(f"python {os.path.abspath(__file__)}")
            exit()
        elif command == 8:
            try:
                os.remove("logs.log")
                print(f"{Colors.OKGREEN}Logs cleared successfully.{Colors.ENDC}\n")
            except FileNotFoundError:
                print(f"{Colors.WARNING}No logs to clear.{Colors.ENDC}\n")
            continue


    comment = f"userInput: {userInput}"
    executionHistory = []
    
    print(f"{Colors.GREY}AI is thinking...{Colors.ENDC}\n")
    responseThink = ""
    print(Colors.GREY, end='', flush=True)
    for chunk in aiClientThink.send(userInput, stream=True):
        print(chunk, end='', flush=True)
        responseThink += chunk
    print(Colors.ENDC)
    print("\n")
    
    responseText = ""
    for chunk in aiClient.send(responseThink, stream=True, immediateExecution=True):
        responseText += str(chunk)
    
    print(Colors.ENDC)
    print(Colors.DIVIDER, Colors.ENDC)
    
    response = aiClient.formatResponse(responseText)
    
    if response is None:
        print(f"{Colors.FAIL}Failed to parse AI response. Please try again.{Colors.ENDC}")
        userInput = input(f"{Colors.OKCYAN}>>>{Colors.ENDC} ")
        continue
    
    comment += f"\n\nAI Response:\n{response}"
    
    if "commands" not in response:
        print(f"{Colors.WARNING}No commands in response.{Colors.ENDC}")
        aiComment = aiClient.comment(comment)
        if not aiComment or not aiComment.strip():
            print(f"{Colors.WARNING}No comment generated by AI (empty response).{Colors.ENDC}")
            print(f"{Colors.GREY}Debug: comment() returned empty string. Check logs.log for details.{Colors.ENDC}\n")
            parts = [""]
        else:
            parts = aiComment.split("**")
        
        result = ""
        for i in range(len(parts)):
            if i % 2 == 1:
                result += Colors.HEADER + Colors.BOLD + parts[i] + Colors.ENDC
            else:
                result += parts[i]
        
        print(result)
        continue
    
    allSuccess = True
    stepNumber = 0
    
    for cmd in response["commands"]:
        stepNumber += 1
        print(f"\n{Colors.OKCYAN}[Step {stepNumber}]{Colors.ENDC}")
        
        confidence = cmd.get("confidence", 100)
        
        if cmd.get("command") == "":
            print(f"{Colors.OKGREEN}{cmd.get('explanation', 'No explanation')}{Colors.ENDC}\n")
            comment += f"\nStep {stepNumber}: {cmd.get('explanation')}"
            continue
        
        if confidence <= 20:
            print(f"{Colors.WARNING}Very low confidence ({confidence}%) - potentially harmful{Colors.ENDC}\n")
            if askMode:
                if not ask(cmd):
                    comment += f"\nStep {stepNumber}: Cancelled by user"
                    continue
                print(f"{Colors.FAIL}Waiting 10 seconds...{Colors.ENDC}\n")
                time.sleep(10)
        
        elif confidence <= 50:
            print(f"{Colors.WARNING}Low confidence ({confidence}%){Colors.ENDC}\n")
            if askMode:
                if not ask(cmd):
                    comment += f"\nStep {stepNumber}: Cancelled by user"
                    continue
        
        if cmd.get("executeImmediately", False) and cmd.get("code", False) != True:
            print(f"{Colors.OKGREEN}Executing immediately: {cmd['command'][:100]}...{Colors.ENDC}\n")
            result = aiClient.executeImmediateCommand(cmd)
            print(f"{Colors.OKCYAN}Result: {result}{Colors.ENDC}\n")
            comment += f"\nStep {stepNumber} (immediate): {result}"
            continue
        
        if cmd.get("code", False):
            print(f"{Colors.OKGREEN}Executing Python code...{Colors.ENDC}\n")
            if askMode:
                if not ask(cmd):
                    comment += f"\nStep {stepNumber}: Code execution cancelled"
                    continue
            
            localVars = {}
            try:
                codeToExec = cmd['command']
                if isinstance(codeToExec, str):
                    codeToExec = codeToExec.encode().decode('unicode_escape')
                stdoutCapture = io.StringIO()
                stderrCapture = io.StringIO()
                compiledCode = compile(codeToExec, '<string>', 'exec')
                with contextlib.redirect_stdout(stdoutCapture), contextlib.redirect_stderr(stderrCapture):
                    exec(compiledCode, localVars, localVars)
                stdoutOutput = stdoutCapture.getvalue()
                result = localVars.get('result', stdoutOutput if stdoutOutput else 'No result variable set.')
                print(f"{Colors.OKGREEN}Code executed successfully.{Colors.ENDC}\n{Colors.OKCYAN}Result: {str(result)}{Colors.ENDC}\n")
                comment += f"\nStep {stepNumber} (Python): Success - {str(result)[:100]}..."
            except Exception as e:
                errorMsg = f"Code execution failed: {e}"
                print(f"{Colors.FAIL}{errorMsg}{Colors.ENDC}")
                comment += f"\nStep {stepNumber} (Python): Failed - {errorMsg}"
                allSuccess = False
                if not cmd.get("continueOnError", False):
                    break
        else:
            print(f"{Colors.OKGREEN}Executing command: {cmd['command'][:100]}...{Colors.ENDC}\n")
            if askMode:
                if not ask(cmd):
                    comment += f"\nStep {stepNumber}: Command execution cancelled"
                    continue
            
            executor = CommandExecutor(dryRun=False, safeMode=False, explain=True)
            result, success = executor.execute(cmd)
            
            if success:
                print(f"{Colors.OKGREEN}Command executed successfully.{Colors.ENDC}\n")
                print(f"{Colors.OKCYAN}Result: {str(result)}{Colors.ENDC}\n")
                if len(str(result)) > 200:
                    print(f"{Colors.GREY}Result (truncated): {str(result)[:200]}...{Colors.ENDC}\n")
                comment += f"\nStep {stepNumber} (Command): Success"
            elif success is False:
                errorMsg = f"Command failed: {str(result)[:200]}"
                print(f"{Colors.FAIL}{errorMsg}{Colors.ENDC}")
                comment += f"\nStep {stepNumber} (Command): Failed - {str(result)[:100]}..."
                allSuccess = False
                if not cmd.get("continueOnError", False):
                    break
            else:
                print(f"{Colors.WARNING}Command was not executed.{Colors.ENDC}\n")
                comment += f"\nStep {stepNumber} (Command): Skipped"
    
    if response.get("nextAction") == "continue":
        print(f"{Colors.OKCYAN}AI suggests to continue. Enter next command or 'done' to finish.{Colors.ENDC}")
        nextInput = input(f"{Colors.OKCYAN}>>>{Colors.ENDC} ")
        if nextInput.lower() != 'done':
            userInput = f"Previous execution completed. Results: {comment[-500:]}. Next: {nextInput}"
            continue
    
    aiComment = aiClient.comment(comment)
    if not aiComment or not aiComment.strip():
        print(f"{Colors.WARNING}No comment generated by AI (empty response).{Colors.ENDC}")
        print(f"{Colors.GREY}Debug: comment() returned empty string. Check logs.log for details.{Colors.ENDC}\n")
        parts = [""]
    else:
        parts = aiComment.split("**")
    result = ""

    for i in range(len(parts)):
        if i % 2 == 1:
            result += Colors.HEADER + Colors.BOLD + parts[i] + Colors.ENDC
        else:
            result += parts[i]

    print(result)

            
    