import uuid
import requests

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

# class Update:
#     def __init__(self, currentVersion):
#         self.currentVersion = currentVersion
#         self.newVersion = None
#         self.changelog = None

#     def display(self):
#         return f"Update available: {self.currentVersion} -> {self.newVersion}"
    
#     def displayChangelog(self):
#         return f"Changelog:\n{self.changelog}"
    
#     def checkForUpdates(self):
#         try:
#             response = requests.get("https://raw.githubusercontent.com/Dequs/HEXEC/refs/heads/main/VERSION")
#             if response.status_code == 200:
#                 latestVersion = response.text.strip()
#                 if latestVersion < self.currentVersion:
#                     if not beta:
#                         print("Your version is corrupted or invalid. Please reinstall the application.")
#                 if latestVersion > self.currentVersion:
#                     self.newVersion = latestVersion
#                     return True
#             return False
#         except Exception:
#             return False
        
#     def applyUpdate(self):
#         if self.newVersion is None:
#             return False
        
#         try:
#             response = requests.get("https://raw.githubusercontent.com/Dequs/HEXEC/refs/heads/main/")
#             if response.status_code == 200:
#                 self.changelog = response.text.strip()
#             return True


    
