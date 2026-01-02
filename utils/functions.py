import uuid
import requests
import zipfile
import os

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

class Update:
    def __init__(self, currentVersion):
        self.currentVersion = currentVersion
        self.newVersion = None
        self.changelog = None
        self.update = False

    def display(self):
        x = ""
        for part in self.newVersion: 
            x += part + "." 
        x = x.rstrip(".")
        return f"Update available: {self.currentVersion} -> {x}" 
    
    def displayChangelog(self):
        return f"Changelog:\n{self.changelog}"
    
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
                        print("Your version is corrupted or invalid. Please reinstall the application.")
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
            print(f"https://github.com/Dequs/HEXEC/releases/download/{x}/HEXEC-{x}.zip")
            print(response.headers['content-type'])
            with open("tmp.zip","wb") as f: f.write(response.content)
            with zipfile.ZipFile("tmp.zip","r") as zip_ref:
                zip_ref.extractall(".")
            os.remove("tmp.zip")
            return True
        except Exception as e:
            print(f"Update failed: {e}")
            return False

class Installation:
    def __init__(self):
        self.list = []
        try:
            import google
        except ImportError:
            self.list.append("google")
        try:
            import colorama
        except ImportError:
            self.list.append("colorama")
        try:
            import uuid
        except ImportError:
            self.list.append("uuid")
        try:
            import zipfile
        except ImportError:
            self.list.append("zipfile")
        try:
            import contextlib
        except ImportError:
            self.list.append("contextlib")
        try:
            import io
        except ImportError:
            self.list.append("io")

    def needsInstallation(self):
        return len(self.list) > 0
    
    def performInstallation(self):
        import subprocess
        try:
            for package in self.list:
                subprocess.check_call(["pip", "install", package])
            return True
        except Exception as e:
            print(f"Installation failed: {e}")
            return False

    
