# Ollama Backend

## Overview
This project is a backend application designed to interact with the Ollama Mistral container. It provides an API for managing the container and facilitates communication between the backend and the containerized service.

## Project Structure
```
ollama-backend
├── src
│   ├── index.ts               # Entry point of the application
│   ├── services
│   │   └── ollamaService.ts   # Service for interacting with the Ollama Mistral container
│   └── utils
│       └── containerManager.ts # Utility for managing Docker containers
├── docker
│   └── Dockerfile              # Dockerfile for building the backend image
├── docker-compose.yml          # Docker Compose configuration for services
├── package.json                # npm configuration file
├── tsconfig.json              # TypeScript configuration file
└── README.md                   # Project documentation
```

## Setup Instructions
1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd ollama-backend
   ```

2. **Install dependencies:**
   ```
   npm install
   ```

3. **Build the Docker image:**
   ```
   docker build -t ollama-backend ./docker
   ```

4. **Run the application using Docker Compose:**
   ```
   docker-compose up
   ```

## Usage
Once the application is running, you can interact with the API endpoints defined in the `src/index.ts` file. The `OllamaService` class in `src/services/ollamaService.ts` provides methods to start, stop, and manage the Ollama Mistral container.

## Integration with Ollama Mistral
This backend application is designed to work seamlessly with the Ollama Mistral container, allowing for efficient management and interaction with the containerized service.

## License
This project is licensed under the MIT License.