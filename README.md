Here’s a clean, professional GitHub-ready **README.md** for your CLI Telegram Client project:

---

# 📟 CLI Telegram Client

A command-line Telegram client with a **Matrix-style interface**, emoji autocorrection, and a unique **Code Mode** for sending messages in programmer-themed styles.

---

## ✨ Features

* **Matrix-Style Interface**: A colorful, aesthetic terminal interface inspired by *The Matrix*, powered by [`rich`](https://github.com/Textualize/rich).
* **Persistent Sessions**: Uses the MTProto protocol (via [`telethon`](https://github.com/LonamiWebs/Telethon)) and securely saves sessions for seamless logins.
* **Interactive Chatting**: Start peer-to-peer chats with any Telegram contact using their username or phone number.
* **Code Mode**: Wrap messages in randomly generated code templates (C, C++, Java, Python) for a geeky chat style.
* **Dynamic Command Prompt**: Prompt updates dynamically to show the current code mode language.
* **Emoji Autocorrection**: Automatically converts shortcuts like `:smile:` or `:heart:` into emojis.
* **Notifications**: Get real-time notifications in the console for new messages.
* **Context-Aware Autocompletion**: Smart autocompletion for commands and emoji shortcuts (powered by [`prompt-toolkit`](https://github.com/prompt-toolkit/python-prompt-toolkit)).

---

## 💻 Technologies Used

* **Python** – Core project language.
* **Telethon** – Implements Telegram API.
* **Rich** – Renders rich text, colors, and panels.
* **Prompt-toolkit** – Provides an advanced interactive terminal input system.
* **Python-dotenv** – Manages API credentials securely.

---

## 🚀 Installation & Setup

### Requirements

* Python **3.8+**
* Dependencies from `requirements.txt`

### Clone & Install

```bash
git clone https://github.com/your-username/tg-cli-project.git
cd tg-cli-project

# Install dependencies
```bash
pip install telethon rich python-dotenv prompt-toolkit
```

### API Credentials

1. Go to [my.telegram.org](https://my.telegram.org).
2. Log in with your phone number.
3. Navigate to **API Development Tools**.
4. Copy your **API\_ID** and **API\_HASH**.

### Run the Client

```bash
python tg-cli.py
```

* On first run, the script will ask for your API credentials and create a `.env` file.

---

## 📝 Commands  

| Command | Description |
|---------|-------------|
| `/chat <username/phone>` | Start a chat session. |
| `/togglecode` | Toggle Code Mode. |
| `/lang <c\|cpp\|java\|python>` | Set code mode language. |
| `/photo <file_path>` | Send a photo. |
| `/back` | Return to main prompt. |
| `/help` | Show help menu. |
| `/exit` | Exit the client. |

---

## 📦 Standalone Executables

Prebuilt binaries (via **PyInstaller**) are available in the [Releases](../../releases) section:

* **Linux**: `tg-cli`
* **Windows**: `tg-cli.exe`

Simply download, place alongside your `.env` file, and run — no installation required.

---

## 📜 License

This project is licensed under the **MIT License**.

---

Would you like me to also **add shields.io badges** (like Python version, license, build status) to make the README more visually appealing?
