# 🐧 #! Remote

**Shebang Remote** is a tool for managing Linux systems remotely via Discord. It integrates with PostgreSQL to store command history, permissions, and user data.

---

## Overview
This system consists of three main components:  

1. **Discord Bot** – Interacts with users, receives commands, and communicates with the web service.  
2. **Web Service** – Hosted on Heroku, handles requests from the bot and agents, stores data in PostgreSQL.  
3. **Agent** – Installed on client machines, executes scripts/commands and reports results back to the web service.  

The architecture allows secure command execution through Discord while maintaining a centralized database of results.

---

## Prerequisites
Before setting up the system, ensure you have:

- Python 3.8 or higher  
- A Heroku account for hosting the web service  
- PostgreSQL database (e.g., Heroku Postgres or local installation)  
- A Discord bot created and configured in the [Discord Developer Portal](https://discord.com/developers/applications)  

---

## Installation Instructions

### Discord Bot
* Create a new application in the Discord Developer Portal.
  * You can find more help [here](https://discordpy.readthedocs.io/en/stable/discord.html#discord-intro)
* Generate a bot token and invite the bot to your server with the appropriate permissions:
  * In the **Settings** sidebar:
    * Click `Bot`
      * Click `Reset token` to generate a new token.
      * Copy the new token. We will use it when configuring Heroku app.
      * Make sure _Public Bot_ and __Message Content Intent_ are checked.
    * Click `OAuth2`
      * In OAuth2 URL Generator / Scopes, select _bot_
      * Then in _Bot Permissions_ select the appropriates permissions:
        * At least _Send Messages_
      * Copy the _Generated URL_ and paste in a new tab to authorize the bot.
        * Add your bot to a server. If you do not have one, create it first and try again.

### Web Service on Heroku
### 🔧 Setup
- **Install Heroku CLI**
- **Clone the repository**
    ```bash
    git clone https://github.com/eliseup/shebang-remote.git
    ```
---

1. Create a new Heroku app:
  * ```bash
    heroku create shebang-remote-api
    ```
    
2. Set up the PostgreSQL add-on or provide your own database URL (`DATABASE_URL`):
  * ```bash
    heroku addons:create heroku-postgresql:essential-0 -a shebang-remote-api
    ```
3. Add Papertrail add-on for logging:
  * ```bash
    heroku addons:create papertrail -a shebang-remote-api
    ```

4. Set environment variables:
  * > Bellow, for `DISCORD_BOT_TOKEN` put the token copied before. For `DISCORD_ADMIN_USER_ID` put the ID of the bot admin user. The bot admin user can be anyone. You can use the bot command `!whoami` to show the current user ID. 
  * ```bash
    heroku config:set APP_SETTINGS_NAME=production APP_SERVER_URL=`heroku info -a shebang-remote-api | grep "Web URL" | awk '{print $3}'` APP_SECRET_KEY=`python3 -c "import os; print(os.urandom(32).hex())"` APP_SECURITY_SALT=`python3 -c "import os; print(os.urandom(16).hex())"` DISCORD_BOT_TOKEN="PUT_YOU_BOT_TOKEN_HERE" DISCORD_ADMIN_USER_ID="ID_OF_THE_BOT_ADMIN_USER" -a shebang-remote-api
    ```

5. Add heroku git remote:
  * ```bash
    heroku git:remote -a shebang-remote-api
    ```

6. * Push changes to heroku repository:
  * ```bash
    git push heroku main
    ```

7. * Scale the process to activate the app:
  * ```bash
    heroku ps:scale web=1 discord=1 -a shebang-remote-api
    ```

> For new subsequents deploys repeat the step 6 only.

### Agent Installation on Ubuntu
> On the target machine: 
- **Clone the repository**
    ```bash
    git clone https://github.com/eliseup/shebang-remote.git
    ```

- **Navigate to the `shebang-remote` directory**
    ```bash
    cd shebang-remote
    ``` 

- **Install the agent**
    ```bash
    sudo ./src/agent-setup.py install
    ``` 
  
- **Register the machine**
  ```bash
  sudo agent.py register --server https://WEB_SERVER_URL
  ```

---

## Usage Instructions

### Example Commands
🔸 **No Auth Required Commands**
    
**!help_**
- _Shows a helper message._
    
**!whoami**
- _Shows the current user info like name and ID._
    
---
    
🔸 **Administrative Commands (Admin users only)**
    
**!admin_allow_user** USER_ID
- _Allow a user to use this bot._
  
**!admin_disallow_user** USER_ID
- _Disallow a user to use this bot._
    
---
    
🔸 **Auth Required Commands**
  
**!list_machines**
- _List all active machines._
  
**!register_script** "SCRIPT_NAME" "SCRIPT_CONTENT"
- _Register a script that can be scheduled later to run on a host._
  > Because the script name and its content may use words with spaces in between, you should quote them.
  
**!execute_script** SCRIPT_NAME MACHINE_ID
- _Schedule the execution of the given script to the given machine._
  > The script name is the same name returned by `!register_script` command.
  > The machine ID can be obtained using `!list_machines` command.

---
---
  
### Verifying Results
To verify a command's result value check the field _output_ in the _command_ table.

### Testing
* Install the agent on a machine;
* Register a script in the bot with the `!register_script` command;
* Execute the script on a registered machine using the `!execute_script` command;
* Verify the output field of the table _command_.

### Security Notes
* Always use HTTPS for communication between bot, web service, and agents.
* Configure environment variables securely from Heroku CLI.

## 🚀 Bonus

---

### 🔧 Development Environment

- **Clone the repository**
    ```bash
    git clone https://github.com/eliseup/shebang-remote.git
    ```

- **Navigate to the `shebang-remote` directory**
    ```bash
    cd shebang-remote
    ``` 

- **Build Docker images and Start the Development Containers**
  - To build the images:
     ```bash
     docker compose -f docker/docker-compose-build-dev.yml build 
     ```
      
  - To start the development environment:
    ```bash
    docker compose -f docker/docker-compose-dev.yml up
    ```
    - You can also run the containers in the background, add the -d flag:
      ```bash
      docker compose -f docker/docker-compose-dev.yml up -d
      ```

- **Create the development src/server/.env_dev file with initial content**
- Use any text editor you prefer.
  - POSTGRES_USER=
  - POSTGRES_PASSWORD=
  - POSTGRES_DB=
  - DB_USER=
  - DB_PASSWORD=
  - DB_NAME=shremote_db
  - DB_HOST=postgresql
  - DB_HOST_PORT=5432
  - APP_SETTINGS_NAME=development
  - APP_SERVER_URL=http://localhost:8000
  - APP_SECRET_KEY=
  - APP_SECURITY_SALT=
  - DISCORD_BOT_TOKEN=
  - DISCORD_ADMIN_USER_ID=


- **Edit the .env_dev file accordingly**
   - Use any text editor you prefer.


- **Access the application container**
   ```bash
   docker exec -it shebang-remote-dev-app-1 bash
   ```

    - **Start the fastapi development application:**
      ```bash
      fastapi dev src/server/main.py --host 0.0.0.0
      ```

**Port Mapping**

- **Container Port**: `8000`
- **Host Port**: `8000`

- Access the server **on the host machine** at `http://localhost:8000`