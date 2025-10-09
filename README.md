# 🐧 #! Shebang Remote

**Shebang Remote** is a tool for managing Linux systems remotely via Discord. It integrates with PostgreSQL to store command history, permissions, and user data.

---

## 🚀 Getting Started

### 🔧 Setup
- **Clone the repository**
    ```bash
    git clone https://github.com/eliseup/shebang-remote.git
    ```

---

### 🔧 Development Environment

After cloning the repository, follow these steps:

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
