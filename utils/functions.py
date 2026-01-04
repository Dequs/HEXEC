import uuid
import requests
import zipfile
import os
from utils.commands import Colors
import sys
import subprocess
import importlib
import logging

logging.basicConfig(
    level=logging.INFO,
    filename="logs.log",
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

beta = False

alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef"

def textToBase42(text):
    data = text.encode("utf-8")
    num = int.from_bytes(data, "big")
    if num == 0:
        return alphabet[0]
    result = ""
    while num > 0:
        num, rem = divmod(num, 42)
        result = alphabet[rem] + result
    return result

def base42ToText(encoded):
    num = 0
    for char in encoded:
        num = num * 42 + alphabet.index(char)
    length = (num.bit_length() + 7) // 8
    return num.to_bytes(length, "big").decode("utf-8")

def textToUUID(text):
    data = text.encode("utf-8")
    num = int.from_bytes(data, "big")
    # ograniczamy do 128 bitów
    num = num & ((1 << 128) - 1)
    return uuid.UUID(int=num)

def uuidToText(u):
    try:
        if isinstance(u, str):
            u = uuid.UUID(u)
        num = u.int
        length = (num.bit_length() + 7) // 8
        return num.to_bytes(length, "big").decode("utf-8")
    except Exception:
        return u
    
def ParseVersion(v):
    v = v.lstrip("v")
    main, *suffix = v.split("-")
    nums = list(map(int, main.split(".")))
    suffix = suffix[0] if suffix else ""
    return nums, suffix

def ask(commands):
    msg_code = f"{Colors.OKGREEN}Code to execute:{Colors.ENDC}\n{commands['command']}\n"
    msg_sep = f"{Colors.HEADER}={Colors.ENDC}" * 30 + "\n"
    msg_expl = f"{Colors.OKBLUE}Explanation:{Colors.ENDC}\n{commands.get('explanation','')}\n"

    print(msg_code)
    print(msg_sep)
    print(msg_expl)

    logger.info("About to execute user-provided code. Explanation: %s", commands.get('explanation'))

    confirm = input(f"{Colors.WARNING}About to execute code above. Proceed? (y/n): {Colors.ENDC}").lower()
    if confirm != 'y':
        logger.info("User cancelled code execution")
        print(f"{Colors.FAIL}Code execution cancelled by user.{Colors.ENDC}")
        return False
    logger.info("User confirmed code execution")
    return True

def changeConsoleTitle(name):
    import ctypes
    ctypes.windll.kernel32.SetConsoleTitleW(name)

class Update:
    def __init__(self, currentVersion):
        self.currentVersion = currentVersion
        self.newVersion = None
        self.changelog = None
        self.update = False
        self.wrong = False

    def display(self):
        x = ""
        for part in self.newVersion: 
            x += part + "." 
        x = x.rstrip(".")
        return f"Update available: {self.currentVersion} -> {x}" 
    
    def displayChangelog(self):
        return f"Changelog:\n{self.changelog}"
    
    def getVersionGithub(self):
        try:
            response = requests.get("https://raw.githubusercontent.com/Dequs/HEXEC/refs/heads/main/VERSION")
            if response.status_code == 200:
                return response.text.strip()
            return None
        except Exception:
            return None
    
    def checkForUpdates(self):
        try:
            response = requests.get("https://raw.githubusercontent.com/Dequs/HEXEC/refs/heads/main/VERSION")
            if response.status_code == 200:
                latestVersion = response.text.strip().split(".")
                currentVersion = self.currentVersion.split(".")
                latestNums, latestSuffix = ParseVersion(response.text.strip())
                currentNums, currentSuffix = ParseVersion(self.currentVersion)
                if latestNums < currentNums:
                    if not beta:
                        logger.warning("Current version appears corrupted or invalid. Consider reinstalling.")
                        print(f"{Colors.FAIL}Current version appears corrupted or invalid. Consider reinstalling.{Colors.ENDC}")
                        self.wrong = True
                if latestNums > currentNums:
                    self.newVersion = latestVersion
                    self.update = True
                    return True
                else:
                    if latestSuffix > currentSuffix:
                        self.newVersion = latestVersion
                        self.update = True
                        return True
            return False
        except Exception:
            return False
        
    def applyUpdate(self):
        if self.newVersion is None:
            return False
        
        try:
            x = ""
            for part in self.newVersion: 
                x += part + "." 
            x = x.rstrip(".")
            response = requests.get(f"https://github.com/Dequs/HEXEC/releases/download/{x}/HEXEC-{x}.zip")
            with open("tmp.zip","wb") as f: f.write(response.content)
            with zipfile.ZipFile("tmp.zip","r") as zip_ref:
                zip_ref.extractall(".")
            os.remove("tmp.zip")
            return True
        except Exception as e:
            logger.exception("Update failed: %s", e)
            return False
        

class Installation:
    def __init__(self):
        self.stdlib = {"uuid", "contextlib", "io", "shutil"}
        self.packages = ["google", "colorama", "uuid", "contextlib", "io", "shutil", "prompt_toolkit"]
        self.missing = []

        for package in self.packages:
            try:
                importlib.import_module(package)
                logger.info("Module available: %s", package)
            except Exception:
                if package not in self.stdlib:
                    self.missing.append(package)

    def needsInstallation(self):
        return len(self.missing) > 0

    def performInstallation(self):
        try:
            for package in self.missing:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", package],
                    check=True
                )
            return True
        except Exception as e:
            logger.exception("Installation failed: %s", e)
            return False


