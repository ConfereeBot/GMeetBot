# 🎥GMeetBot
## Table of Contents
- [🎥GMeetBot](#gmeetbot)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Endpoints](#endpoints)
  - [📩Message Format](#message-format)
    - [Request Format (Producer)](#request-format-producer)
    - [Response Format (Consumer)](#response-format-consumer)
  - [📡RabbitMQ Topics](#rabbitmq-topics)
  - [🚀Usage](#usage)
  - [🛠️Installing project in DEBUG mode](#️installing-project-in-debug-mode)
  - [📦App deployment](#app-deployment)

## Overview
This project is a Dockerized Python application that emulates video and audio drivers for recording purposes. It uses nodriver to launch Chrome and record Google Meet conferences. The application is managed via a RabbitMQ message broker.

## Endpoints
In addation, it deploys web-server on FastApi in order to upload contents to a client. Photos are not stored, videos vice verse — stored in docker volume.
- `/download/{filename}` — request for downloading contents
- Use port `12390` for VNC, `12396` — for web-server

## 📩Message Format
### Request Format (Producer)
```json
{
    "type": "screenshot | time | stop",
    "body": "<data>",
    "user_id": "<user_id>",
    "filepath": "<file_path>"
}
```
- `type`: One of the Req commands:
  - `screenshot`: Capture a screenshot.
  - `time`: Retrieve the current timestamp.
  - `stop`: Stop the recording.

### Response Format (Consumer)
```json
{
    "type": "started | error | succeded | busy",
    "body": "<data>",
    "user_id": "<user_id>",
    "filepath": "<file_path>"
}
```
- `type`: One of the Res responses:
    - `started`: Recording started successfully.
    - `error`: An error occurred.
    - `succeded`: Recording completed successfully.
    - `busy`: The system is currently busy.

## 📡RabbitMQ Topics
- `gmeet_tasks`: Queue for recording tasks. Send here request for starting record
- `gmeet_manage`: Queue for control commands. Send here request for managing record
- `gmeet_res`: Queue for responses. Response is sent here

## 🚀Usage
- ▶️ To start recording, send a Req.START message to `gmeet_tasks`.
- 🖼 To take a screenshot, send a Req.SCREENSHOT message to `gmeet_manage`.
- ⛔ To stop recording, send a Req.STOP_RECORD message to `gmeet_manage`.
- 📬 Responses will be received with Res statuses on `gmeet_res`.

## 🛠️Installing project in DEBUG mode
1. Make sure you have `poetry` and *docker desktop* installed
2. Run docker engine
3. `git clone https://github.com/ConfereeBot/GMeetBot.git`
4. `poetry install`
5. `pre-commit install`
6. Choose appropriate configuration in "Run and Debug"
7. Run debug (`f5` in vs code)

## 📦App deployment
1. Clone `git clone https://github.com/ConfereeBot/GMeetBot.git && cd GMeetBot`
2. Configure `.env` in the current folder
3. Run project `docker compose up -d --build`
