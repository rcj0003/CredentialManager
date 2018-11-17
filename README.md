# CredentialManager
## Changelog
### 1.0.0
- First release

### 1.0.1
- Fixed a type with the refreshConnection() function.

### 1.0.2
- Fixed an issue with command parsing in Main() and in JUtils.py.

### 2.0.0
- Fixed an issue where the script did not function in other environments properly.
- Added a check to see if the MySQL connector is installed.
- Fixed an issue where user data was cached with username instead of user ID.
- Renamed the 'exit' command to 'logout'. (Backwards incompatible fix)
- Made some changes to how deleteById() and deleteByUsername() worked.

### The Sessions Update (3.0.0)
- Added the 'login' command with the optional argument to auto-login from a config in the same directory.
- Added 'fluid' mode option, which is disabled by default. It reverts the login-logout system to the old system if enabled.
- The CommandProcessor class has been updated. One method has been added that is now required to be used by all commands (the '.isEnabled()' method). Another method (the '.getDisableReason()') is required if '.isEnabled()' ever returns False. (Backwards incompatible fix)

### Fluidity Update (3.1.0)
- Re-added the 'exit' command as a new, separate functioning command that closes the terminal.
- Exceptions that occur are now logged in the isIdAvailable() method.
- The login command now returns a proper message when the command is not executable (instead of saying unknown reason).
- You can now specify "{database}.config" or "{database}" with the login command to load the "{database}.config" file. Ex: "login database" or "login database.config" uses "database.config" as its config.
- Other miscelleanous bug fixes.

### Power Update (4.0.0)
- Switched from JUtils to JUtils2
    - Added numerous commands
    - Removed some unnecessary functions that are now covered by JUtils2
    - Added the ability to use scripts, variables, etc.
    - The transition is currently incomplete, expect more integration with JUtils2 in later updates

### 4.1.0
- Some commands now store results as variables.
- Updated to JUtils2 v0.5.0.
- Bug fixes.

### 5.0.0-alpha
- Fluid-mode has been removed.
- Updated to JUtils2 0.8.0.
- There is a slight change in how user data is saved when gracefully closing the connection.
