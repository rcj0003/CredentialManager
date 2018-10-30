# === [ JUtils v3.0.0 ] === #
# Created by Ryan Jones @ 2018

import shlex
import time
import traceback

class Utils():
    def strToIntList(string):
        return list(map((lambda x: ord(x)), string))

    def intListToStr(data):
        string = ""
        for x in data:
            string += chr(x)
        return string

    # A simple form of encryption (using the XOR operator) I discovered by accident a few years back (in another language).
    def xorCrypto(data, key):
        if type(data) is str:
            data = Utils.strToIntList(data)

        if type(key) is str:
            key = Utils.strToIntList(key)
    
        if type(data) is list:
            offset = 0
            for x in range(0, len(data)):
                data[x] ^= key[offset]
                offset = offset + 1 if offset + 1 < len(key) else 0
            
            return data

    def dictionaryToTupleList(dictionary):
        plist = []
        for x in dictionary.keys():
            plist.append((x, dictionary[x]))
        return plist

    def tupleListToDictionary(tupleList):
        dictionary = {}
        for x in tupleList:
            dictionary.update({x[0]: x[1:]})
        return dictionary

    def getCommandArguments(string):
        data = shlex.split(string)
        return (data[0].lower(), data[1:] if len(data) >= 2 else [])

    def getSystemTime():
        return int(round(time.time() * 1000))

    def logExceptionToFile(filename):
        with open(filename, "a") as fileWrite:
            fileWrite.write(traceback.format_exc() + "\n")
            fileWrite.close()

class HelpCommand():
    def __init__(self, processor):
        self.processor = processor

    def getName(self):
        return "help"

    def execute(self, args):
        if len(args) == 0:
            print("\n===[Commands Help]===")
            for command in self.processor.getRegisteredCommands():
                name = command.getName().title()
                desc = command.getShortDescription()
                print(f"{name}: {desc}")
            print()
        else:
            search = args[0]
            results = self.processor.getCommandsByName(search)
            print("\n===[Commands Help]===")
            print(str(len(results)) + f" results were found with the search term \'{search}\'.\n")
            for command in results:
                name = command.getName().title()
                usage = command.getUsage()
                arguments = str(command.getMinimumArguments())
                desc = "\n".join(command.getLongDescription())
                print(f"{name} Command:\nUsage: {usage}\nMinimum arguments: {arguments}\n{desc}\n")

    def getMinimumArguments(self):
        return 0
    
    def getUsage(self):
        return "help (search)"
    
    def getShortDescription(self):
        return "Lists all commands in detail."
    
    def getLongDescription(self):
        return ["Lists all commands in detail.", "Specific commands can be searched as an optional argument."]

    def isEnabled(self):
        return True

class CommandProcessor():
    def getDisabledReason(command):
        try:
            return command.getDisableReason()
        except:
            return "Unknown reason."
        
    def __init__(self, commands = {}):
        self.commands = commands

    def executeCommand(self, command, args = []):
        try:
            if type(command) is str:
                command = self.commands[command]
        except:
            print("Unknown command. Try the 'help' command for a detailed list of commands.")
            return

        if len(args) < command.getMinimumArguments():
            print("Usage: () indicates an optional argument, [] indicates a required argument:\n" + command.getUsage())
        else:
            if command.isEnabled():
                command.execute(args)
            else:
                reason = CommandProcessor.getDisabledReason(command)
                print(f"This command has been disabled! [{reason}]")

        return self

    def registerCommand(self, *command):
        for c in command:
            self.commands.update({c.getName().lower(): c})
        return self

    def deregisterCommand(self, command):
        self.commands.pop(command)
        return self

    # Returns the command registered by name if it exists, otherwise None is returned
    def getExactCommandByName(self, name):
        try:
            return self.commands[name.lower()]
        except:
            return None

    # More like a search, it returns a list of commands that contain 'name'.
    def getCommandsByName(self, name):
        return list(map((lambda x: x[1]), filter((lambda x: name in x[0]), Utils.dictionaryToTupleList(self.commands))))

    # Returns all registered commands as a list.
    def getRegisteredCommands(self):
        return list(self.commands.values())
