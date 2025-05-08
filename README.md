# RetroCloud
Co-authors: Jorge Garrido AND David Garcia  
This is a project to create an accesible interface to storage and download your saved games on a server on your own raspberry with a database that would help us search games and save profiles

the intended functionality is to have a web page as a user interface, and save or download our own games, mods, or patches.
This way, we could reliably acces to our games wereever we are.
## Project planning
### Tasks:

* DATA BASE
  * sql
    * ID
    * Name
    * game system
    * company
    * File route
    * Users
* FRONT
  * front page
  * SignIn / LogIn
  * search engine (sql)
  * company selection
  * system selection
  * Game Selection
  * Downloader
+ FILE SISTEM
  * File per company
    * File per System
      * File per game (with updates and DLC and mods)
  * Everithing .zip
* SERVER
  * create a partition on the raspberry with proxmox or  Ubuntu
  * save the file sistem with routes on the raspberry
  * RASPBERRY CONNECTION
  * static router port and VPN for easy connection
  * using file transfer protocol ftp (security not needed)

Comando para levatar el servidor:
```
python -m uvicorn main:app --reload
```