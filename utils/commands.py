import subprocess
from colorama import Fore
import logging

logging.basicConfig(
    level=logging.INFO,
    filename="logs.log",
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

class Colors:
    HEADER = Fore.MAGENTA
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

class CommandExecutor:
    def __init__(self, dryRun=False, safeMode=True, explain=True):
        logger.info("Initializing CommandExecutor.")
        self.dryRun = dryRun
        self.safeMode = safeMode
        self.explain = explain

    def setDryRun(self, dryRun: bool):
        logger.info(f"Setting dry run mode to: {dryRun}")
        self.dryRun = dryRun

    def getDryRun(self) -> bool:
        logger.info(f"Getting dry run mode: {self.dryRun}")
        return self.dryRun

    def execute(self, command: dict):
        logger.info(f"Executing command: {command['command']}")
        if self.dryRun:
            logger.info("Dry run mode enabled, not executing command.")
            print(f"{Colors.WARNING}[DRY RUN] Command to execute: {Colors.ENDC}" + str(command.get('command', '')))
            return "Dry run - command not executed.", None

        if command["danger"] and self.safeMode:
            logger.warning("Command marked as dangerous and safe mode is enabled. Blocking execution.")
            return f"{Colors.FAIL}Command execution blocked for safety reasons.{Colors.ENDC}", None

        logger.info("Executing command in shell.")
        try:
            if command.get("timeout"):
                print(f"{Colors.WARNING}Note: This command may take a long time to execute.{Colors.ENDC}")
            result = subprocess.run(
                command["command"],
                shell=True,
                input="y\n",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=None if command.get("timeout") is True else 30
            )
            output = result.stdout if result.stdout else result.stderr
            logger.info("Command executed successfully.")
            if self.explain:
                explanation = command["explanation"]
                logger.info("Providing explanation for command execution.")
                return f"\n{Colors.OKGREEN}Command executed successfully.{Colors.ENDC}\n{output}\n{Colors.OKCYAN}Explanation:\n{explanation}", True
            return f"{Colors.HEADER}{output}{Colors.ENDC}", True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error executing command: {e.stderr}")
            return f"{Colors.FAIL}Error executing command:{Colors.ENDC}\n{e.stderr}", False
        except subprocess.TimeoutExpired:
            logger.error("Command execution timed out.")
            return f"{Colors.FAIL}Command execution timed out.{Colors.ENDC}", False
        
class InteractiveExecutor:
    def __init__(self, aiClient, streamMode=True):
        self.aiClient = aiClient
        self.streamMode = streamMode
        self.command_history = []

    def executeWithFeedback(self, user_input):
        print(f"{Colors.OKCYAN}Starting interactive execution...{Colors.ENDC}")

        while True:
            response = self.aiClient.send(user_input, stream=self.streamMode)

            commandData = self.aiClient.formatResponse(response)
            if not commandData or "commands" not in commandData:
                return "No valid command received"

            for cmd in commandData["commands"]:
                executor = CommandExecutor()
                result, success = executor.execute(cmd)

                self.command_history.append({
                    "command": cmd.get("command", ""),
                    "result": result,
                    "success": success
                })

                if self.streamMode:
                    print(f"\n{Colors.OKGREEN}Command executed{Colors.ENDC}")
                    print(f"{Colors.GREY}Result: {str(result)[:200]}...{Colors.ENDC}")

                if not success and not (cmd.get("continueOnError", False) or cmd.get("continue_on_error", False)):
                    return f"Command failed: {result}"

            user_input = "Previous command executed. Provide next command or say 'complete' if finished."
        