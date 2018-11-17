# ==={ JUtils 2 by Ryan Jones }=== #
# Release Date: 11/17/2018

import hashlib as sha
import datetime
import time
import traceback
import shlex
import sys

storedVariables = {}

class Compatibility():
    """Provides simple methods to aid with compatibility."""
    def getVersion():
        """Returns a tuple providing the major, minor, patch, and pre-release identifier like so: (Major, Minor, Patch, Identifier)"""
        return (0, 6, 0, "")

    def getVersionString():
        """Returns the version in the following format: Major.Minor.Patch(-Pre-release Indetifier)\nThe identifier may be absent if the release is a full release."""
        versionData = Compatibility.getVersion()
        return ("%s.%s.%s" % versionData[:-1]) + ("" if len(versionData[3]) == 0 else "-%s" % versionData[3])

    def getSimpleVersion():
        """Returns a tuple providing the major, minor, and patch information for easier handing of compatibility."""
        return Compatibility.getVersion()[:-1]

    def getMajorVersion():
        """Returns the major version number."""
        return Compatibility.getVersion()[0]

class AdvancedMap():
    """Provides a simple methods to map and filter objects without having to nest and cast excessively."""
    def __init__(self, *results):
        self.results = []
        for x in results:
            if type(x) is iter:
                self.results += list(x)
            else:
                self.results += x

    def __iter__(self):
        for x in self.results:
            yield x

    def __len__(self):
        return len(self.results)

    def __add__(self, other):
        if type(other) is AdvancedMap:
            self.results = self.results + other.getResults()
        elif type(other) is list:
            self.results = self.results + other
        else:
            self.results.append(other)
        return self

    def __iadd__(self, other):
        if type(other) is AdvancedMap:
            self.results = self.results + other.getResults()
        elif type(other) is list:
            self.results = self.results + other
        else:
            self.results.append(other)
        return self

    def __repr__(self):
        return "AdvancedMap(%s)" % self.results
        
    def mapData(self, function, data):
        """Does the same thing as map(), but it casts `data` to a list, the results are stored as a list to be editted or retrieved with other functions.\n'function' - Either a lambda function or a pre-defined function to be used for mapping.\n'data' - Some iterable data structure that can be cast to a list."""
        self.results = list(map(function, list(data)))
        return self
    
    def mapResults(self, function):
        """Does the same thing as map(), but re-maps the stored results with function given.\n'function' - Either a lambda function or a pre-defined function to be used for mapping."""
        return self.mapData(function, self)

    def selectivelyMapResults(self, filterFunction, mapFunction):
        """Using 'filterFunction', only the elements filtered for true will be remapped with 'mapFunction'."""
        plist = Utilities.createEmbeddedList(range(0, len(self)), self)
        AdvancedMap(plist).filterResults(lambda x: filterFunction(x[1])).forEach(lambda x: AdvancedMap.__setElementAt(self.results, x[0], mapFunction(x[1])))
        return self

    def __setElementAt(plist, index, newElement):
        # Internal function so we can do an assignment operator in a lambda, normally not allowed.
        plist[index] = newElement

    def addMapToResults(self, function, data):
        """Maps the data provided using the function, and then adds it to the stored results.\n'function' - Either a lambda function or a pre-defined function to be used for mapping.\n'data' - Some iterable data structure that can be cast to a list."""
        self.results += list(map(function, list(data)))
        return self
    
    def filterResults(self, function):
        """Filters stored results using the function provided, and thus alters the final result.\n'function' - The function used to filter the stored results."""
        self.results = self.getFilteredResults(function)
        return self

    def forEach(self, function):
        """Executes the given function and passes each stored result as a parameter."""
        for x in self:
            function(x)
        return self

    def getResults(self):
        """Returns the results of all maps and filters."""
        return self.results
    
    def getFilteredResults(self, function):
        """Returns the results of all maps and filters, and filters them. Stored results are not affected.\n'function' - Lambda expression or function to filter the data with."""
        return list(filter(function, self.results))

    def clearResults(self):
        """Clears stored results."""
        self.results.clear()
        return self

class Utilities():
    """Provides an assortment of functions and tools used frequently."""
    def tryParse(value, otherwise = 0):
        """Parses value to an integer, otherwise it returns the 0 or the second parameter."""
        try:
            return int(value)
        except:
            return otherwise

    def replaceAll(string, values):
        """Parses string to replace all values (%value%) with their corresponding dictionary value."""
        for x in values.keys():
            if values.get(x, None) != None:
                string = string.replace(f"%{x}%", str(values[x]))
        return string

    def convertStringToHash(string):
        """Returns a SHA256 hash from a string."""
        return sha.sha256(string.encode(encoding="UTF-16")).hexdigest()
    
    def logTracebackToFile(filename):
        """Logs the most recent traceback to a file named 'filename'."""
        with open(filename, "a") as fileWrite:
            fileWrite.write(Utilities.getSystemTimeString() + "\n" + traceback.format_exc())

    def getSystemTime():
        """Returns the system time in milliseconds."""
        return int(round(time.time() * 1000))

    def getSystemTimeString():
        """Returns a string based on the current system time."""
        return Utilities.getStringFromTimestamp(Utilities.getSystemTime())

    def getStringFromTimestamp(time):
        """Converts a timestamp in milliseconds to a string."""
        return str(datetime.datetime.fromtimestamp(time / 1000))
    
    def stringToIntList(string):
        """Converts a string to an integer list. The elements correspond to the character code in the original string."""
        return AdvancedMapMap().mapData(lambda x: ord(x), string).getResults()

    def intListToString(intList):
        """Converts an integer list into a string."""
        return "".join(AdvancedMap().mapData(lambda x: chr(x), intList).getResults())

    def xorCrypto(key, data):
        """Encrypts 'data' with 'key' using symmetric XOR encryption."""
        if type(data) is str:
            data = Utilities.stringToIntList(data)

        if type(key) is str:
            key = Utilities.stringToIntList(key)
    
        if type(data) is list:
            offset = 0
            for x in range(0, len(data)):
                data[x] ^= key[offset]
                offset = offset + 1 if offset + 1 < len(key) else 0
            
            return data

    def parseCommand(string):
        """Splits and parses a string into a useable command format in tuple form, with the first element being the main command, and the second being a list of arguments. "command test" would return ("command", ["test"])"""
        data = shlex.split(string)
        return ("", []) if len(data) == 0 else (data[0].lower(), data[1:] if len(data) >= 2 else [])

    def getParsedInput(dialog):
        """Returns a tuple with the primary command as the first element and the arguments (list form) as the second element."""
        while True:
            commandInput = input(dialog)
            if len(commandInput.replace(" ", "")) == 0:
                continue
            return Utilities.parseCommand(commandInput)

    def createEmbeddedList(keys, values):
        """Creates an embedded list, using each key as the first element and each value as the second element in each sub-list."""
        return list(map(lambda x, y: [x, y], keys, values))
    
    def createTupleList(keys, values):
        """Creates a tuple list, using each key as the first element and each value as the second element in each tuple."""
        return list(map(lambda x, y: (x, y), keys, values))
    
    def createDictionary(keys, values):
        """Creates a dictionary given keys and values."""
        return dict(map(lambda x, y: (x, y), keys, values))

class CommandProcessor2():
    """Functions similarly to JUtils' CommandProcessor class, but it builds upon it and improves."""
    def __init__(self, commands = {}):
        self.commands = commands
        self.queue = []

    def queueCommands(self, commands):
        """Input a list of commands, either parsed or non-parsed, to be queue and executed later."""
        self.queue += AdvancedMap(commands).selectivelyMapResults(lambda x: type(x) is str, lambda x: Utilities.parseCommand(x)).getResults()

    def forceQueueCommands(self, commands):
        """Does the same thing as queueCommands, but forces the inputted commands to the front of the queue."""
        self.queue = AdvancedMap(commands).selectivelyMapResults(lambda x: type(x) is str, lambda x: Utilities.parseCommand(x)).getResults() + self.queue

    def executeNextInQueue(self):
        """Execute stored commands."""
        if not self.isQueueClear():
            command = self.queue.pop(0)
            self.executeCommand(command[0], command[1])
        return not(len(self.queue) == 0)

    def isQueueClear(self):
        """Returns true if the command queue is clear."""
        return len(self.queue) == 0

    def clearCommandQueue(self):
        """Clears command queue."""
        self.queue.clear()

    def executeCommands(self, commands):
        """Input a list of commands, either parsed or non-parsed, to be executed."""
        AdvancedMap(commands).selectivelyMapResults(lambda x: type(x) is str, lambda x: Utilities.parseCommand(x)).forEach(lambda x: self.executeCommand(x[0], x[1]))

    def executeCommand(self, command, args = []):
        """Input a command and its arguments to execute the command."""
        global storedVariables
        args = AdvancedMap(args).mapResults(lambda x: Utilities.replaceAll(x, storedVariables)).getResults()
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
                reason = command.getDisabledReason()
                print(f"This command has been disabled! [{reason}]")
        return self

    def registerCommands(self, commands):
        """Input a list of commands to be registered."""
        self.commands.update(Utilities.createDictionary(AdvancedMap(commands).mapResults(lambda x: x.getName().lower()).getResults(), commands))
        return self

    def deregisterCommand(self, command):
        """Input a command to be deregistered."""
        self.commands.pop(command)
        return self

    def getExactCommandByName(self, name):
        """Returns an exact command by name."""
        try:
            return self.commands[name.lower()]
        except:
            return None
    
    def getCommandsByName(self, name):
        """Returns a list of commands that contain 'name' in their name."""
        return AdvancedMap(Utilities.createEmbeddedList(self.commands.keys(), self.commands.values())).filterResults(lambda x: name.lower() in x[0]).mapResults(lambda x: x[1]).getResults()

    def getRegisteredCommands(self):
        """Returns a list of all registered commands."""
        return list(self.commands.values())

# === Standalone Script === #
class JUtilsCommand():
    def getName(self):
        return "jutils"

    def execute(self, args):
        print("\n===[JUtils2]===")
        print("Author: Ryan Jones")
        print("Version: " + Compatibility.getVersionString())
        print()

    def getMinimumArguments(self):
        return 0
    
    def getUsage(self):
        return "jutils"
    
    def getShortDescription(self):
        return "Gives specific information about the JUtils2 currently being run."
    
    def getLongDescription(self):
        return ["Gives specific information about the JUtils2 currently being run."]

    def isEnabled(self):
        return True

class HelpCommand():
    def __init__(self, processor):
        self.processor = processor

    def getName(self):
        return "help"

    def execute(self, args):
        if len(args) == 0:
            print("\n===[Commands Help]===")
            for command in self.processor.getRegisteredCommands():
                name = command.getName().lower()
                desc = command.getShortDescription()
                print(f"{name}: {desc}")
            print()
        else:
            search = args[0]
            results = self.processor.getCommandsByName(search)
            print("\n===[Commands Help]===")
            print(str(len(results)) + f" results were found with the search term \'{search}\'.\n")
            for command in results:
                name = command.getName().lower()
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

class DefineCommand():
    def getName(self):
        return "define"

    def execute(self, args):
        global storedVariables
        storedVariables.update({args[0]: "" if len(args) == 1 and not(args[0] in storedVariables) else args[1]})

    def getMinimumArguments(self):
        return 1
    
    def getUsage(self):
        return "define [variable] [value]"
    
    def getShortDescription(self):
        return "Defines a string variable to store in memory."
    
    def getLongDescription(self):
        return ["Defines a string variable to store in memory."]

    def isEnabled(self):
        return True

class DefineIntCommand():
    def getName(self):
        return "defint"

    def execute(self, args):
        global storedVariables
        storedVariables.update({args[0]: 0 if len(args) == 1 and not(args[0] in storedVariables) else Utilities.tryParse(args[1], -1)})

    def getMinimumArguments(self):
        return 1
    
    def getUsage(self):
        return "defint [variable] (value)"
    
    def getShortDescription(self):
        return "Defines an integer variable to store in memory."
    
    def getLongDescription(self):
        return ["Defines a integer variable to store in memory.", "The value is optional, you can simply declare"]

    def isEnabled(self):
        return True

class AddCommand():
    def getName(self):
        return "add"

    def execute(self, args):
        global storedVariables
        try:
            if type(storedVariables[args[0]]) is int:
                storedVariables[args[0]] += Utilities.tryParse(args[1], 0)
            else:
                storedVariables[args[0]] += args[1]
        except:
            pass

    def getMinimumArguments(self):
        return 2
    
    def getUsage(self):
        return "add [variable] [value]"
    
    def getShortDescription(self):
        return "Adds 'value' to 'variable'."
    
    def getLongDescription(self):
        return ["Adds 'value' to 'variable'."]

    def isEnabled(self):
        return True

class ConditionalCommand():
    def __init__(self, processor):
        self.processor = processor
    
    def getName(self):
        return "conditional"

    def execute(self, args):
        global storedVariables
        if str(storedVariables[args[0]]) == args[1]:
            self.processor.forceQueueCommands(args[2:])

    def getMinimumArguments(self):
        return 3
    
    def getUsage(self):
        return "conditional [variable] [value] [commands...]"
    
    def getShortDescription(self):
        return "Executes the commands if variable equals value."
    
    def getLongDescription(self):
        return ["Executes the commands if variable equals value."]

    def isEnabled(self):
        return True

class CompareCommand():
    def getName(self):
        return "compare"

    def execute(self, args):
        global storedVariables
        try:
            if args[1] == ">":
                if type(storedVariables[args[0]]) is int:
                    storedVariables.update({"results": "true" if storedVariables[args[0]] > Utilities.tryParse(args[2]) else "false"})
                    return
            if args[1] == ">=":
                if type(storedVariables[args[0]]) is int:
                    storedVariables.update({"results": "true" if storedVariables[args[0]] >= Utilities.tryParse(args[2]) else "false"})
                    return
            if args[1] == "=":
                if type(storedVariables[args[0]]) is int:
                    storedVariables.update({"results": "true" if storedVariables[args[0]] == Utilities.tryParse(args[2]) else "false"})
                    return
            if args[1] == "<":
                if type(storedVariables[args[0]]) is int:
                    storedVariables.update({"results": "true" if storedVariables[args[0]] < Utilities.tryParse(args[2]) else "false"})
                    return
            if args[1] == "<=":
                if type(storedVariables[args[0]]) is int:
                    storedVariables.update({"results": "true" if storedVariables[args[0]] <= Utilities.tryParse(args[2]) else "false"})
                    return 
        except:
            pass
        storedVariables.update({"results": "false"})

    def getMinimumArguments(self):
        return 3
    
    def getUsage(self):
        return "compare [variable] [comparison operator] [value]"
    
    def getShortDescription(self):
        return "Stores the result of variable the command in the results variable."
    
    def getLongDescription(self):
        return ["Stores the result of variable being greater than value in the results variable."]

    def isEnabled(self):
        return True

class PrintCommand():
    def getName(self):
        return "print"

    def execute(self, args):
        AdvancedMap(args).forEach(lambda x: print(x))

    def getMinimumArguments(self):
        return 1
    
    def getUsage(self):
        return "print [message]"
    
    def getShortDescription(self):
        return "Prints a message on screen."
    
    def getLongDescription(self):
        return ["Prints a message on screen.", "Use %VariableName% to insert stored variable values."]

    def isEnabled(self):
        return True

class RunScriptCommand():
    def __init__(self, processor):
        self.processor = processor
    
    def getName(self):
        return "run"

    def execute(self, args):
        try:
            commands = []
            with open(args[0], "r") as fileRead:
                commands = AdvancedMap(fileRead).mapResults(lambda x: x.strip()).filterResults(lambda x: len(x) > 0).getResults()
            global storedVariables
            self.processor.clearCommandQueue()
            self.processor.forceQueueCommands(commands)
        except IOError:
            print("The script does not exist!")
        except:
            print("An error occurred while trying to run the script.")

    def getMinimumArguments(self):
        return 1
    
    def getUsage(self):
        return "run [file/script]"
    
    def getShortDescription(self):
        return "Executes the commands in the given script."
    
    def getLongDescription(self):
        return ["Executes the commands in the given script."]

    def isEnabled(self):
        return True

class WaitCommand():
    def getName(self):
        return "wait"

    def execute(self, args):
        start = Utilities.getSystemTime()
        time = 1000 if len(args) == 0 else Utilities.tryParse(args[0], 1000)
        while start + time > Utilities.getSystemTime():
            pass

    def getMinimumArguments(self):
        return 0
    
    def getUsage(self):
        return "wait"
    
    def getShortDescription(self):
        return "Waits the specified milliseconds."
    
    def getLongDescription(self):
        return ["Waits the specified milliseconds."]

    def isEnabled(self):
        return True

class ClearMemoryCommand():
    def getName(self):
        return "clearmem"

    def execute(self, args):
        global storedVariables
        storedVariables.clear()
        print("Memory cleared!")

    def getMinimumArguments(self):
        return 0
    
    def getUsage(self):
        return "clearmem"
    
    def getShortDescription(self):
        return "Clears all stored variables."
    
    def getLongDescription(self):
        return ["Clears all stored variables."]

    def isEnabled(self):
        return True

class VariablesCommand():
    def getName(self):
        return "vars"

    def execute(self, args):
        global storedVariables
        print("{:^30}|{:^30}".format("Variable", "Value"))
        print("-" * 61)
        for variable in storedVariables.keys():
            displayVariable = variable if len(variable) < 28 else variable[:25] + "..."
            value = str(storedVariables[variable])
            displayValue = value if len(value) < 28 else variable[:25] + "..."
            print(" {: <29}| {: <29}".format(displayVariable, displayValue))

    def getMinimumArguments(self):
        return 0
    
    def getUsage(self):
        return "vars"
    
    def getShortDescription(self):
        return "Prints a list of all stored variables and their values."
    
    def getLongDescription(self):
        return ["Prints a list of all stored variables and their values."]

    def isEnabled(self):
        return True

class ExitCommand():
    def getName(self):
        return "exit"

    def execute(self, args):
        sys.exit()

    def getMinimumArguments(self):
        return 0
    
    def getUsage(self):
        return "exit"
    
    def getShortDescription(self):
        return "Closes the terminal."
    
    def getLongDescription(self):
        return ["Closes the terminal."]

    def isEnabled(self):
        return True

def runTerminal(header = "", commands = []):
    global storedVariables
    storedVariables = {}
    processor = CommandProcessor2()
    print(header)
    processor.registerCommands([JUtilsCommand(), HelpCommand(processor), RunScriptCommand(processor), DefineCommand(), DefineIntCommand(), CompareCommand(), AddCommand(), PrintCommand(), ConditionalCommand(processor), WaitCommand(), VariablesCommand(), ClearMemoryCommand(), ExitCommand()] + commands)
    while True:
        parsedCommand = Utilities.getParsedInput("> ")
        processor.executeCommand(parsedCommand[0], parsedCommand[1])
        while processor.executeNextInQueue():
            pass

if __name__ == "__main__":
    runTerminal("[JUtils2 v" + Compatibility.getVersionString() + "]\nCreated by Ryan Jones @ 2018\n\nUse the 'help' command for a detailed list of commands.\n")
