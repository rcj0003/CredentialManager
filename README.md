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
