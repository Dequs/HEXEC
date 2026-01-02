from utils.client import AI
from utils.config import Config
from colorama import Fore
from utils.commands import CommandExecutor
from utils.functions import uuidToText, Update
import contextlib
import io
import os

os.system("cls")

class Colors:
    HEADER = Fore.LIGHTBLUE_EX
    OKBLUE = Fore.BLUE
    OKCYAN = Fore.CYAN
    OKGREEN = Fore.GREEN
    WARNING = Fore.YELLOW
    FAIL = Fore.RED
    ENDC = Fore.RESET
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

with open("VERSION", "r") as versionFile:
    currentVersion = versionFile.read().strip()

update = Update(currentVersion)
check = update.checkForUpdates()

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
                                                  
    {update.display() if update.checkForUpdates() else f"Current version: {currentVersion} (up to date)"}                                               
    Created by: {Colors.OKBLUE}Mateusz Rudnik (rudnikos3000){Colors.ENDC}
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

config = Config()
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
    Config.createConfig(settings)

x = 1

chats = {}

print(f"\n{Colors.HEADER}{'='*50}{Colors.ENDC}")
print(f"{Colors.OKGREEN}Available Chats:{Colors.ENDC}\n")

for file in os.listdir("chats"):
    print(f"  {Colors.OKBLUE}[{x}]{Colors.ENDC} {Colors.OKBLUE}{file.split(".elham")[0]}{Colors.ENDC}")
    print(f"      {Colors.OKCYAN}Created: {uuidToText(file.split(".elham")[0])}{Colors.ENDC}")
    chats[x] = file
    x += 1

print(f"\n  {Colors.OKGREEN}[{x}]{Colors.ENDC} {Colors.OKGREEN}Start new chat{Colors.ENDC}")
if x+1 <= 2:
    pass
else:
    print(f"  {Colors.FAIL}[{x+1}]{Colors.ENDC} {Colors.FAIL}Delete all chat histories{Colors.ENDC}")

print(f"\n{Colors.HEADER}{'='*50}{Colors.ENDC}")
choice = int(input(f"\n{Colors.OKCYAN}>>> {Colors.ENDC}"))

os.system("cls")

print(f"{Colors.OKGREEN}Selected chat: {chats[choice] if choice in chats else 'New Chat'}{Colors.ENDC}")

if choice == x + 1:
    try:
        for file in os.listdir("chats"):
            os.remove(f"chats/{file}")
        print(f"{Colors.OKGREEN}All chat histories deleted successfully.{Colors.ENDC} Restarting program...\n")
    except FileNotFoundError:
        print(f"{Colors.WARNING}No chat histories to delete.{Colors.ENDC}\n")
    exit()
    
config = Config()
apiKey = config.get("API_KEY")
model = config.get("model")
askMode = config.get("alwaysAsk")
apiKeyComment = config.get("API_KEY_COMMENT")

aiClient = AI(api_key=apiKey, model=model, api_key_comment=apiKeyComment, chat=chats[choice].split(".elham")[0] if choice in chats else None)
aiClient.setPrompt("prompt.txt")

while True:
    userInput = input(f"{Colors.OKCYAN}>>>{Colors.ENDC} ")

    internalCommands = ["exit", "config", "cls", "clear", "history", "reset"]

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


    comment = f"userInput: {userInput}"

    while True:
        response = aiClient.send(userInput)
        try:
            response = aiClient.formatResponse(response)
        except Exception as e:
            print(f"{Colors.FAIL}Error parsing response JSON: {str(e)[:100]}{Colors.ENDC}")
            print(f"{Colors.WARNING}Please try your request again.{Colors.ENDC}")
            userInput = input(f"{Colors.OKCYAN}>>>{Colors.ENDC} ")
            continue

        if response is None:
            print(f"{Colors.FAIL}Failed to parse AI response. Please try again.{Colors.ENDC}")
            userInput = input(f"{Colors.OKCYAN}>>>{Colors.ENDC} ")
            continue

        comment += f"\n\nAI Response:\n{response}"

        allSuccess = True

        for commands in response["commands"]:
            if commands["command"] == "":
                print(f"{Colors.OKGREEN}{commands['explanation']}{Colors.ENDC}\n")
                continue
            if commands["code"] == True:
                if askMode:
                    print(f"{Colors.OKGREEN}Code to execute:{Colors.ENDC}\n{commands['command']}\n")
                    confirm = input(
                        f"{Colors.WARNING}About to execute code above. Proceed? (y/n): {Colors.ENDC}"
                    ).lower()
                    if confirm != 'y':
                        print(f"{Colors.FAIL}Code execution cancelled by user.{Colors.ENDC}")
                        comment += f"\n\nCode execution cancelled by user for code:\n{commands['command']}"
                        continue
                local_vars = {}
                try:
                        code_to_exec = commands['command'].replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')
                        stdout_capture = io.StringIO()
                        stderr_capture = io.StringIO()
                        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
                            exec(code_to_exec, globals(), local_vars)
                        stdout_output = stdout_capture.getvalue()
                        result = local_vars.get('result', stdout_output if stdout_output else 'No result variable set.')
                        #print(f"{Colors.OKGREEN}Code executed successfully. Result:{Colors.ENDC}\n{result}\n")
                        comment += f"\n\nCode executed successfully. Result:\n{result}"
                except Exception as e:
                        print(f"{Colors.FAIL}Code execution failed: {e}{Colors.ENDC}")
                        userInput = f"Code execution failed: {e}"
                        allSuccess = False
                        comment += f"\n\nCode execution failed:\n{e}"
                        break
                continue
            if askMode:
                confirm = input(
                    f"{Colors.WARNING}About to execute command:{Colors.ENDC} {commands['command']}\nProceed? (y/n): "
                ).lower()
                if confirm != 'y':
                    print(f"{Colors.FAIL}Command execution cancelled by user.{Colors.ENDC}")
                    comment += f"\n\nCommand execution cancelled by user for command: {commands['command']}"
                    continue

            #print(f"{Colors.OKGREEN}Executing command:{Colors.ENDC} {commands['command']}")
            executor = CommandExecutor(dryRun=False, safeMode=False, explain=True)
            result, success = executor.execute(commands)

            if success:
                #print(result)
                comment += f"\n\nCommand executed successfully:\n{result}"
            elif success is False:
                print(f"{Colors.FAIL}Command failed, sending error to AI...{Colors.ENDC}")
                userInput = f"Command failed: {result}"
                allSuccess = False
                comment += f"\n\nCommand failed:\n{result}"
                break
            elif success is None:
                print(f"{Colors.WARNING}Command was not executed.{Colors.ENDC}")
                comment += f"\n\nCommand was not executed:\n{result}"

        if allSuccess:
            break

    
    aiComment = aiClient.comment(comment)
    print(f"{Colors.OKBLUE}{aiComment}{Colors.ENDC}\n")

            
    