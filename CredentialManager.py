# === [ Credential Manager v5.0.0-alpha ] === #
# Created by Ryan Jones @ 2018

# Versioning follows the Sematic Versioning 2.0 format: https://semver.org/

# 1.0.1
# - Fixed a typo in the 'refreshConnection()' function.

# 1.0.2
# - Fixed an issue with command parsing in Main() and in JUtils.py.

# 2.0.0
# - Fixed an issue where the script did not function in other environments properly.
# - Added a check to see if the MySQL connector is installed.
# - Fixed an issue where user data was cached with username instead of user ID.
# - Renamed the 'exit' command to 'logout'. (Backwards incompatible fix)
# - Made some changes to how deleteById() and deleteByUsername() worked.

# The Sessions Update (3.0.0)
# - Added the 'login' command with the optional argument to auto-login from a config in the same directory.
# - Added 'fluid' mode option, which is disabled by default. It reverts the login-logout system to the old system if enabled.
# - The CommandProcessor class has been updated. One method has been added that is now required to be used by all commands (the '.isEnabled()' method). Another method (the '.getDisabledReason()') is required if '.isEnabled()' ever returns False. (Backwards incompatible fix)

# Fluidity Update (3.1.0)
# - Added the 'exit' command.
# - Exceptions that occur are now logged in the isIdAvailable() method.
# - The login command now returns a proper message when the command is not executable (instead of saying unknown reason).
# - You can now specify "{database}.config" or "{database}" with the login command to load the "{database}.config" file. Ex: "login database" or "login database.config" uses "database.config" as its config.
# - Other miscelleanous bug fixes.

# Power Update (4.0.0)
# - Switched from JUtils to JUtils2
    # - Added numerous commands
    # - Removed some unnecessary functions that are now covered by JUtils2
    # - Added the ability to use scripts, variables, etc.
    # - The transition is currently incomplete, expect more integration with JUtils2 in later updates

# 4.1.0
# - Some commands now store results as variables.
# - Updated to JUtils2 v0.5.0.
# - Bug fixes.

# 5.0.0-alpha
# - Fluid-mode has been removed.
# - Updated to JUtils2 0.8.0.
# - There is a slight change in how user data is saved when gracefully closing the connection.

import JUtils2 as jutils
import msvcrt
import csv
import sys
import os

try:
    import mysql.connector as sql
except:
    print("\n[ERROR] The 'MySQL Connector for Python' module is missing!\nYou can download it from here: https://dev.mysql.com/downloads/connector/python/\n")
    while True:
        pass

info = None
connection = None
cursor = None

# === Primary classes and functions == #

class DatabaseInfo():
    def getFromFile(database = "database.config"):
        try:
            data = []
            with open(f"{database}" if database.endswith(".config") else f"{database}.config", "r") as fileRead:
                fileContents = csv.reader(fileRead, delimiter=",")
                data = list(fileContents)[0]
            return DatabaseInfo(data[0], data[1], data[2], data[3], data[4])
        except:
            return None
    
    def __init__(self, ip, port, database, username, password):
        self.ip = ip
        self.port = port
        self.database = database
        self.__username = username
        self.__password = password

    def getDatabase(self):
        return (self.ip, self.port, self.database)

    def attemptConnection(self):
        global connection
        global cursor
        try:
            connection = sql.connect(host=self.ip,port=self.port,database=self.database,user=self.__username,passwd=self.__password)
            cursor = connection.cursor()
            return True
        except:
            if connection != None:
                connection.close()
                connection = None
            jutils.Utilities.logTracebackToFile("errors.log")
            return False

class CredentialManager():
    # Let's reduce the number of database calls by caching the data locally.
    __cache = {}

    def setup():
        global cursor
        cursor.execute("CREATE TABLE IF NOT EXISTS `Credential_Table` (id VARCHAR(16), username VARCHAR(16), pwhash VARCHAR(256), nickname VARCHAR(16), role VARCHAR(16), creation BIGINT, locked BOOLEAN)")
    
    # Its a good idea to 'poll' your databases from time to time with selection queries and reopen them if an exception is thrown for a known working connection.
    # From my experience, most databases automatically close connections after long periods of inactivity (24ish hours usually) and begin throwing exceptions.
    def refreshConnection():
        global cursor
        global info
        try:
            cursor.execute("SELECT * FROM `Credential_Table`")
            results = cursor.fetchall()
        except:
            connection.close()
            info.attemptConnection()
            jutils.Utilities.logTracebackToFile("errors.log")

    def gracefulExit():
        global connection
        global cursor
        
        # Save all cached user data.
        AdvancedMap(CredentialManager.__cache.values()).forEach(CredentialManager.updateUser)

        connection.close()
        cursor.close()

        CredentialManager.__cache.clear()
        
    def createUser(user):
        CredentialManager.refreshConnection()
        try:
            global cursor
            global connection
            cursor.execute("INSERT INTO `Credential_Table` (id,username,pwhash,nickname,role,creation,locked) VALUES (%(id)s,%(username)s,%(pwhash)s,%(nickname)s,%(role)s,%(creation)s,%(locked)s)", user.getDictionaryData(True))
            connection.commit()
        except:
            jutils.Utilities.logTracebackToFile("errors.log")
            print("An unknown error occurred.")

    def isIdAvailable(userId):
        CredentialManager.refreshConnection()
        try:
            global cursor
            cursor.execute("SELECT * FROM `Credential_Table` WHERE id=%(id)s LIMIT 1", {"id": userId})
            return len(cursor.fetchall()) == 0
        except:
            jutils.Utilities.logTracebackToFile("errors.log")
            return False

    def isUsernameAvailable(username):
        CredentialManager.refreshConnection()
        try:
            global cursor
            cursor.execute("SELECT * FROM `Credential_Table` WHERE username=%(username)s LIMIT 1", {"username": username})
            return len(cursor.fetchall()) == 0
        except:
            jutils.Utilities.logTracebackToFile("errors.log")
            return False

    def deleteById(userId):
        user = getUserById(userId)
        if user != None:
            CredentialManager.deleteUser(user)

    def deleteByUsername(username):
        user = getUserByName(username)
        if user != None:
            CredentialManager.deleteUser(user)
    
    def getUserById(userId, useCache = True):
        if useCache and (userId in CredentialManager.__cache.keys()):
            return CredentialManager.__cache[userId]
        
        CredentialManager.refreshConnection()
        
        try:
            global cursor
            cursor.execute("SELECT * FROM `Credential_Table` WHERE id=%(id)s LIMIT 1", {"id": userId})
            return resultsToUser(cursor.fetchall()[0])
        except:
            jutils.Utilities.logTracebackToFile("errors.log")
            return None

    def getUserByName(username, useCache = True):
        if useCache:
            for user in CredentialManager.__cache.values():
                if user.getUsername() == username:
                    return user

        CredentialManager.refreshConnection()
        
        try:
            global cursor
            cursor.execute("SELECT * FROM `Credential_Table` WHERE username=%(username)s LIMIT 1", {"username": username})
            return CredentialManager.resultsToUser(cursor.fetchall()[0])
        except:
            jutils.Utilities.logTracebackToFile("errors.log")
            return None

    def resultsToUser(results):
        user = User(results[0], results[1], results[3], results[4], results[5], results[6])
        CredentialManager.__cache.update({user.getUniqueID(): user})
        return user

    def updateUser(user, updatePassword = False):
        CredentialManager.refreshConnection()
        try:
            global cursor
            global connection

            if updatePassword and user.getPasswordHash() != None:
                cursor.execute("UPDATE `Credential_Table` SET pwhash = %(pwhash)s, nickname = %(nickname)s, role = %(role)s, creation = %(creation)s, locked = %(locked)s WHERE id = %(id)s", user.getDictionaryData(True))
                user.setPasswordHash(None)
            else:
                cursor.execute("UPDATE `Credential_Table` SET nickname = %(nickname)s, role = %(role)s, creation = %(creation)s, locked = %(locked)s WHERE id = %(id)s", user.getDictionaryData(False))

            connection.commit()
        except:
            jutils.Utilities.logTracebackToFile("errors.log")
            print("An error occurred when saving the record.")

    def deleteUser(user):
        CredentialManager.refreshConnection()
        try:
            global cursor
            global connection

            cursor.execute("DELETE FROM `Credential_Table` WHERE id = %(id)s", {"id": user.getUniqueID()})
            connection.commit()
            CredentialManager.__cache.pop(user.getUniqueID())
        except:
            jutils.Utilities.logTracebackToFile("errors.log")
            print("An error occurred while deleting the user's data.")

    def getUserInfoList():
        CredentialManager.refreshConnection()
        try:
            global cursor
            global connection

            cursor.execute("SELECT id,username FROM `Credential_Table`")

            return cursor.fetchall()
        except:
            jutils.Utilities.logTracebackToFile("errors.log")
            print("An error occurred while deleting the user's data.")

class User():
    def __init__(self, userId, username, nickname, role, creationDate, isLocked):
        self.cooldown = 0
        self.userId = userId
        self.username = username
        self.__pwHash = None
        self.nickname = nickname
        self.role = role
        self.creationDate = creationDate
        self.locked = isLocked

    def getUniqueID(self):
        return self.userId

    def getUsername(self):
        return self.username

    def getNickname(self):
        return self.nickname

    def setNickname(self, nickname):
        self.nickname = nickname

    def getRole(self):
        return self.role

    def setRole(self, role):
        self.role = role

    def getCreationDate(self):
        return self.creationDate

    def isLocked(self):
        return self.locked

    def setLocked(self, locked):
        self.locked = locked

    def setPasswordHash(self, pwHash):
        self.__pwHash = pwHash

    def getPasswordHash(self):
        return self.__pwHash

    def getDictionaryData(self, fullData = False):
        if fullData:
            return {"id": self.userId, "username": self.username, "pwhash": self.__pwHash, "nickname": self.nickname, "role": self.role, "creation": self.creationDate, "locked": self.locked}
        else:
            return {"id": self.userId, "username": self.username, "nickname": self.nickname, "role": self.role, "creation": self.creationDate, "locked": self.locked}         

def getCredential(msg, header = "", ignoreAlphanumeric = False, acceptNone = False, maxSize = -1, clearAfter = True, clearFirst = True):
    if clearFirst:
        clearScreen()
    while True:
        print(header)
        credential = input(msg)
        if isCredential(credential, ignoreAlphanumeric, acceptNone, maxSize):
            if clearAfter:
                clearScreen()
            return credential if credential != "" else None
        clearScreen()

def isCredential(credential, ignoreAlphanumeric, acceptNone, maxSize):
    return (maxSize == -1 or (len(credential) <= maxSize)) and (credential.isalnum() or ignoreAlphanumeric) and (acceptNone or credential != "")

def getDatabaseCredentials(autologin = True, file = "database"):
    global info

    info = DatabaseInfo.getFromFile(file) if autologin else None

    while True:
        if info == None:
            ip = getCredential("IP Address: ", "CredentialManager [5.0.0-alpha]\nRyan Jones @ 2018\n\nPlease login to your database to continue.\n", ignoreAlphanumeric = True)
            port = getCredential("Port Number: ", "CredentialManager [5.0.0-alpha]\nRyan Jones @ 2018\n\nPlease login to your database to continue.\n")
            db = getCredential("Database name: ", "CredentialManager [5.0.0-alpha]\nRyan Jones @ 2018\n\nPlease login to your database to continue.\n", ignoreAlphanumeric = True)
        
            username = getCredential("Username: ", "CredentialManager [5.0.0-alpha]\nRyan Jones @ 2018\n\nPlease login to your database to continue.\n")
            pw = getCredential("Password: ", "CredentialManager [5.0.0-alpha]\nRyan Jones @ 2018\n\nPlease login to your database to continue.\n", ignoreAlphanumeric = True)

            info = DatabaseInfo(ip, port, db, username, pw)

        print("Attempting connection...\n")
        
        if info.attemptConnection():
            clearScreen()
            break
        else:
            info = None
            print("Connection failed!\n")

def clearScreen(msg = None):
    os.system('cls')
    if msg != None:
        print(msg)

def awaitConfirmation(question = "Is this ok? Y/N"):
    print(question)
    return msvcrt.getwch().lower() == "y"

def createUser():
    userId = ""
    username = ""
    pwHash = ""
    nickname = ""
    role = ""
    locked = False

    clearScreen()
    
    while True:
        userId = getCredential("Enter a unique user ID for your new user (16 characters max): ", "CredentialManager [5.0.0-alpha]\nRyan Jones @ 2018\n", maxSize = 16)

        clearScreen("Checking availability...\n")

        if CredentialManager.isIdAvailable(userId):
            print("ID available.\n")
            break
        else:
            print("This user ID is in use!\n")

    while True:
        username = getCredential("Enter a unique username for your new user (16 characters max): ", "CredentialManager [5.0.0-alpha]\nRyan Jones @ 2018\n", maxSize = 16)

        clearScreen("Checking availability...\n")

        if CredentialManager.isIdAvailable(username):
            print("Username available.\n")
            break
        else:
            print("This username is in use!\n")

    pwHash = jutils.Utilities.convertStringToHash(getCredential("Enter a password for your new user (16 characters max): ", "CredentialManager [5.0.0-alpha]\nRyan Jones @ 2018\n", ignoreAlphanumeric = True, maxSize = 16))

    nickname = getCredential("(Optional) Enter a nickname for your new user (16 characters max): ", "CredentialManager [5.0.0-alpha]\nRyan Jones @ 2018\n", ignoreAlphanumeric = True, acceptNone = True, maxSize = 16)
    role = getCredential("(Optional) Enter a role for your new user (16 characters max): ", "CredentialManager [5.0.0-alpha]\nRyan Jones @ 2018\n", ignoreAlphanumeric = True, acceptNone = True, maxSize = 16)

    locked = awaitConfirmation("Should the user's account be locked initially? Y to lock, N to leave unlocked.")

    if awaitConfirmation("Should the new user's data be applied to the database? Y to save their data, N to discard it."):
        print("Saving to database...\n")
        user = User(userId, username, nickname, role, jutils.Utilities.getSystemTime(), locked)
        user.setPasswordHash(pwHash)
        CredentialManager.createUser(user)
        print("Operation complete!\n")

def isConnected():
    global connection
    return connection != None and connection.is_connected()

# === Commands Section === #
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
        return not isConnected()

    def getDisabledReason(self):
        return "You must be logged out to use this command."

class LoginCommand():
    def getName(self):
        return "login"

    def execute(self, args):
        clearScreen()
        getDatabaseCredentials(len(args) > 0, "database" if len(args) == 0 else args[0])
        clearScreen("CredentialManager [5.0.0-alpha]\nRyan Jones @ 2018\n\nUse the 'help' command for details on how to use commands.\n")
        CredentialManager.setup()
        jutils.storedVariables.update({"logged-in": "true"})

    def getMinimumArguments(self):
        return 0
    
    def getUsage(self):
        return "login (Credential Config)"
    
    def getShortDescription(self):
        return "Logs into a database."
    
    def getLongDescription(self):
        return ["Use this to log into a database.", "You can auto-login into a database by supplying an argument", "specifying a '.config' to use for credentials."]

    def isEnabled(self):
        return not isConnected()

    def getDisabledReason(self):
        return "You cannot log into another server whilest being connected to another!"

class ConnectedCommand():
    def isEnabled(self):
        return isConnected()

    def getDisabledReason(self):
        return "Please connect to a MySQL server to use this command."

class UserlistCommand(ConnectedCommand):
    def getName(self):
        return "userlist"

    def execute(self, args):
        print("{:^17}|{:^17}".format("Unique ID", "Username"))
        print("-" * 35)
        
        for userdata in CredentialManager.getUserInfoList():
            print(" {: <16}| {: <16}".format(userdata[0], userdata[1]))

    def getMinimumArguments(self):
        return 0
    
    def getUsage(self):
        return "userlist"
    
    def getShortDescription(self):
        return "Lists all users and their unique IDs."
    
    def getLongDescription(self):
        return ["Lists all users and their unique IDs."]

class ResetPasswordCommand(ConnectedCommand):
    def getName(self):
        return "resetpw"

    def execute(self, args):
        username = args[0]
        user = CredentialManager.getUserByName(args[0])

        if user == None:
            print("\nThis user does not exist!\n")
            return

        user.setPasswordHash(convertStringToHash(getCredential("Enter a new password for the user: (16 characters max): ", "CredentialManager [5.0.0-alpha]\nRyan Jones @ 2018\n", ignoreAlphanumeric = True, maxSize = 16)))
        user.setLocked(True)

        CredentialManager.updateUser(user)

        clearScreen("User's password was successfully reset.")

    def getMinimumArguments(self):
        return 1
    
    def getUsage(self):
        return "resetpw [Username]"
    
    def getShortDescription(self):
        return "Resets a user's password and locks their account."
    
    def getLongDescription(self):
        return ["Resets a user's password and locks their account."]

class SetRoleCommand(ConnectedCommand):
    def getName(self):
        return "setrole"

    def execute(self, args):
        username = args[0]
        user = CredentialManager.getUserByName(args[0])

        if user == None:
            print("\nThis user does not exist!\n")
            return

        user.setRole(getCredential("Enter a new role for the user: (16 characters max): ", "CredentialManager [5.0.0-alpha]\nRyan Jones @ 2018\n", ignoreAlphanumeric = True, acceptNone = True, maxSize = 16, clearAfter = False))

        CredentialManager.updateUser(user)

        print(f"{username}'s role has been updated.")

    def getMinimumArguments(self):
        return 1
    
    def getUsage(self):
        return "setrole [Username]"
    
    def getShortDescription(self):
        return "Sets a user's role."
    
    def getLongDescription(self):
        return ["Sets a user's role."]

class SetNickCommand(ConnectedCommand):
    def getName(self):
        return "setnick"

    def execute(self, args):
        username = args[0]
        user = CredentialManager.getUserByName(args[0])

        if user == None:
            print("\nThis user does not exist!\n")
            return

        user.setNickname(getCredential("Enter a new nickname for the user: (16 characters max): ", "CredentialManager [5.0.0-alpha]\nRyan Jones @ 2018\n", ignoreAlphanumeric = True, acceptNone = True, maxSize = 16, clearAfter = False))

        CredentialManager.updateUser(user)

        print(f"{username}'s nickname has been updated.")

    def getMinimumArguments(self):
        return 1
    
    def getUsage(self):
        return "setnick [Username]"
    
    def getShortDescription(self):
        return "Sets a user's nickname."
    
    def getLongDescription(self):
        return ["Sets a user's nickname."]

class DetailUserCommand(ConnectedCommand):
    def getName(self):
        return "detailuser"

    def execute(self, args):
        username = args[0]
        user = CredentialManager.getUserByName(args[0])

        if user == None:
            print("\nThis user does not exist!\n")
            return

        print("\n===[User Info]===")
        print("Username:      " + user.getUsername())
        print("Unique ID:     " + user.getUniqueID() + "\n")
        if user.getNickname() != None:
            print("Nickname:      " + user.getNickname())
        if user.getRole() != None:
            print("Role:          " + user.getRole() + "\n")
        print("Creation Date: " + jutils.Utilities.getStringFromTimestamp(user.getCreationDate()))
        print("Locked?        " + "Yes" if user.isLocked() else "No")
        
        jutils.storedVariables.update({"username": user.getUsername(), "unique-id": user.getUniqueID(), "nickname": user.getNickname() if user.getNickname() != None else "", "role": user.getRole() if user.getRole() != None else "", "creation-timestamp": jutils.Utilities.getStringFromTimestamp(user.getCreationDate()), "locked": "Yes" if user.isLocked() else "No"})

        print()

    def getMinimumArguments(self):
        return 1
    
    def getUsage(self):
        return "detailuser [Username]"
    
    def getShortDescription(self):
        return "Gives you a snapshot of user data."
    
    def getLongDescription(self):
        return ["Gives you a snapshot of user data."]

class LockUserCommand(ConnectedCommand):
    def getName(self):
        return "lock"

    def execute(self, args):
        username = args[0]
        user = CredentialManager.getUserByName(args[0])

        if user == None:
            print("\nThis user does not exist!\n")
            return
        
        locked = awaitConfirmation(f"\n{username}\'s account is currently " + ("locked" if user.isLocked() else "unlocked") + ". Would you like to lock? Y to lock, N to unlock.")

        user.setLocked(locked)
        CredentialManager.updateUser(user)

        print(f"\n{username}\'s account was set to " + ("Locked" if locked else "Unlocked") + ".\n")

    def getMinimumArguments(self):
        return 1
    
    def getUsage(self):
        return "lock [Username]"
    
    def getShortDescription(self):
        return "Allows you to set whether or not a user is locked."
    
    def getLongDescription(self):
        return ["Allows you to set whether or not a user is locked.", "Y locks the account, N unlocks it."]

class DeleteUserCommand(ConnectedCommand):
    def getName(self):
        return "deleteuser"

    def execute(self, args):
        username = args[0]
        user = CredentialManager.getUserByName(args[0])

        if user == None:
            print("\nThis user does not exist!\n")
            return

        if awaitConfirmation(f"\nWould you like to delete '{username}'? This is not reversible. Y deletes the user, N cancels."):
            CredentialManager.deleteUser(user)
            print(f"{username}'s account was deleted.\n")
        else:
            print("Operation canceled.\n")

    def getMinimumArguments(self):
        return 1
    
    def getUsage(self):
        return "deleteuser [Username]"
    
    def getShortDescription(self):
        return "Deletes a user from the given username."
    
    def getLongDescription(self):
        return ["Deletes a user from the given username.", "Nothing happens if the username does not exist."]

class LogoutCommand(ConnectedCommand):
    def getName(self):
        return "logout"

    def execute(self, args):
        CredentialManager.gracefulExit()
        jutils.storedVariables.update({"logged-in": "false"})
        print("\nYou have been logged out of the database.\n")

    def getMinimumArguments(self):
        return 0
    
    def getUsage(self):
        return "logout"
    
    def getShortDescription(self):
        return "Properly saves user data, logs out, and exits gracefully."
    
    def getLongDescription(self):
        return ["Properly saves user data, logs out, and exits gracefully.", "You should always use this command upon completion of your tasks."]

class CreateUserCommand(ConnectedCommand):
    def getName(self):
        return "createuser"

    def execute(self, args):
        createUser()

    def getMinimumArguments(self):
        return 0
    
    def getUsage(self):
        return "createuser"
    
    def getShortDescription(self):
        return "Starts a prompt to create a new user."
    
    def getLongDescription(self):
        return ["Starts a prompt to create a new user.", "The prompt is relatively secure, as the screen is cleared", "as each credential is entered."]
    
class ClearCommand():
    def getName(self):
        return "clear"

    def execute(self, args):
        clearScreen("Console has been cleared!")

    def getMinimumArguments(self):
        return 0
    
    def getUsage(self):
        return "clear"
    
    def getShortDescription(self):
        return "Clears the console."
    
    def getLongDescription(self):
        return ["Clears the console."]

    def isEnabled(self):
        return True

# === Main Section === #
if __name__ == "__main__":
    if "idlelib" in sys.modules:
        print("\n===[Compatibility Error]===\nThis program is only compatible when run through Windows terminal.\n")
        sys.exit()
    
    jutils.storedVariables.update({"logged-in": "false"})
    jutils.runTerminal("CredentialManager [5.0.0-alpha]\nRyan Jones @ 2018\n\nUse the 'help' command for details on how to use commands.\n", [ClearCommand(), CreateUserCommand(), DeleteUserCommand(), LockUserCommand(), SetRoleCommand(), SetNickCommand(), ResetPasswordCommand(), UserlistCommand(), DetailUserCommand(), ExitCommand(), LoginCommand(), LogoutCommand()])
