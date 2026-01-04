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
    DIVIDER = f"{HEADER}="*30, f"{ENDC}\n"

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
            print(f"{Colors.WARNING}[DRY RUN] Command to execute: {Colors.ENDC}{command["command"]}")
            return "Dry run - command not executed.", None

        if command["danger"] and self.safeMode:
            logger.warning("Command marked as dangerous and safe mode is enabled. Blocking execution.")
            return f"{Colors.FAIL}Command execution blocked for safety reasons.{Colors.ENDC}", None

        logger.info("Executing command in shell.")
        try:
            if command["timeout"]:
                print(f"{Colors.WARNING}Note: This command may take a long time to execute.{Colors.ENDC}")
            result = subprocess.run(
                command["command"],
                shell=True,
                input="y\n",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=0 if command["timeout"] is True else 30
            )
            output = result.stdout
            logger.info("Command executed successfully.")
            if self.explain:
                explanation = command["explanation"]
                logger.info("Providing explanation for command execution.")
                return f"{Colors.OKGREEN}Command executed successfully.{Colors.ENDC}\n{output}\n{Colors.OKCYAN}Explanation:\n{explanation}", True
            return f"{Colors.OKGREEN}Command executed successfully.{Colors.ENDC}\n{output}", True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error executing command: {e.stderr}")
            return f"{Colors.FAIL}Error executing command:{Colors.ENDC}\n{e.stderr}", False
        except subprocess.TimeoutExpired:
            logger.error("Command execution timed out.")
            return f"{Colors.FAIL}Command execution timed out.{Colors.ENDC}", False
        