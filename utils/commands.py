import subprocess
from colorama import Fore

class Colors:
    HEADER = Fore.MAGENTA
    OKBLUE = Fore.BLUE
    OKCYAN = Fore.CYAN
    OKGREEN = Fore.GREEN
    WARNING = Fore.YELLOW
    FAIL = Fore.RED
    ENDC = Fore.RESET
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class CommandExecutor:
    def __init__(self, dryRun=False, safeMode=True, explain=True):
        self.dryRun = dryRun
        self.safeMode = safeMode
        self.explain = explain

    def setDryRun(self, dryRun: bool):
        self.dryRun = dryRun

    def getDryRun(self) -> bool:
        return self.dryRun

    def execute(self, command: dict):
        if self.dryRun:
            print(f"{Colors.WARNING}[DRY RUN] Command to execute: {Colors.ENDC}{command["command"]}")
            return "Dry run - command not executed.", None

        if command["danger"] and self.safeMode:
            return f"{Colors.FAIL}Command execution blocked for safety reasons.{Colors.ENDC}", None

        try:
            result = subprocess.run(command["command"], shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
            output = result.stdout
            if self.explain:
                explanation = command["explanation"]
                return f"{Colors.OKGREEN}Command executed successfully.{Colors.ENDC}\n{output}\n{Colors.OKCYAN}Explanation:\n{explanation}", True
            return f"{Colors.OKGREEN}Command executed successfully.{Colors.ENDC}\n{output}", True
        except subprocess.CalledProcessError as e:
            return f"{Colors.FAIL}Error executing command:{Colors.ENDC}\n{e.stderr}", False
        