# This script creates a full-featured, CLI-based Telegram client.
#
# Key features:
# - Connects to the Telegram API as a user using MTProto (via Telethon).
# - Persists login session across runs.
# - Provides a "Matrix-style" console interface using the rich library.
# - Allows you to open a peer-to-peer chat session with any user.
# - Messages are timestamped and color-coded.
# - You can toggle a "code mode" to wrap messages in a C program template.
# - Supports sending photos with the `/photo` command.
# - Marks messages as read automatically.
# - Displays messages from other chats as notifications.
# - Includes a /help command for guidance.
#
# To run this script:
# 1. Install the necessary libraries:
#    pip install telethon rich python-dotenv prompt-toolkit
# 2. Get your API ID and API Hash:
#    Go to https://my.telegram.org and log in.
#    Click on "API development tools" to get your credentials.
# 3. Create a .env file in the same directory with your API_ID and API_HASH.
# 4. Run the script: python cli_telegram_client.py
# 5. On the first run, it will prompt you for your phone number and verification code.

import asyncio
import sys
import os
import re
from telethon import TelegramClient, events
from telethon.tl.types import User, Channel, Chat
from rich.console import Console
from rich.theme import Theme
from rich.text import Text
from datetime import datetime
from dotenv import load_dotenv
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.completion import WordCompleter

# ==================== CONFIGURATION ====================
# Load environment variables from the .env file
load_dotenv()

# You MUST replace these with your own API ID and API Hash.
API_ID = int(os.getenv('API_ID', '0'))
API_HASH = os.getenv('API_HASH', '')
# =======================================================

# Define a custom theme for Rich to match the desired aesthetics
cli_theme = Theme({
    "info": "dim green",
    "prompt": "bold magenta",
    "incoming": "cyan",
    "outgoing": "green",
    "timestamp": "dim white",
    "error": "bold red",
    "notification": "yellow"
})

# Initialize the Rich Console with the custom theme
console = Console(theme=cli_theme)

# Session name for persistent login
SESSION_NAME = 'cli_session'

# Global state variables for the chat session and display
current_peer_entity = None
is_code_mode = False
client = None

# ==================== UTILITY FUNCTIONS ====================

def clear_screen():
    """Clears the console screen."""
    console.clear()

def get_formatted_time():
    """Returns the current timestamp in HH:MM:SS format."""
    return datetime.now().strftime('%H:%M:%S')

def encode_to_c_code(message):
    """Encodes a message into a C program template."""
    # Escape double quotes to prevent breaking the C string
    escaped_message = message.replace('"', '\\"')
    c_code = f"""#include <stdio.h>

int main() {{
    printf("{escaped_message}\\n");
    return 0;
}}
"""
    # Wrap the code in markdown for nice formatting
    return f"```c\n{c_code}\n```"

def show_help():
    """Prints the list of available commands."""
    console.print("\n[bold]Available Commands:[/bold]")
    console.print("  [yellow]/chat <username/phone>[/yellow] - Start a new chat session.")
    console.print("  [yellow]/togglecode[/yellow] - Toggle C code encoding mode.")
    console.print("  [yellow]/photo <file_path>[/yellow] - Send a photo from a file.")
    console.print("  [yellow]/back[/yellow] - Return to peer selection from an active chat.")
    console.print("  [yellow]/help[/yellow] - Show this help message.")
    console.print("  [yellow]/exit[/yellow] - Log out and exit the client.")
    console.print("\n[info]Messages from other chats will appear as notifications.[/info]")

# ==================== MAIN LOGIC FUNCTIONS ====================

async def chat_with_peer(peer_entity, session):
    """Manages the interactive chat session with a specific peer."""
    global is_code_mode, current_peer_entity
    
    current_peer_entity = peer_entity
    peer_name = getattr(peer_entity, "first_name", None) or "Unknown"
    
    console.print(f"\n[bold yellow]Chat session with {peer_name} started.[/bold yellow]")
    console.print("[info]Commands: /back, /togglecode, /photo <file>, /help[/info]\n")

    while True:
        try:
            user_input = await session.prompt_async("[prompt]> ")
        except (EOFError, KeyboardInterrupt):
            current_peer_entity = None
            console.print("[info]Exiting chat session.[/info]\n")
            break
        
        user_input = user_input.strip()

        if not user_input:
            continue

        if user_input.lower() == "/back":
            current_peer_entity = None
            console.print("[info]Exiting chat session.[/info]\n")
            break

        elif user_input.lower() == "/togglecode":
            is_code_mode = not is_code_mode
            status = "ON" if is_code_mode else "OFF"
            console.print(f"[info]Code mode {status}[/info]")
            continue

        elif user_input.lower().startswith("/photo"):
            try:
                file_path = user_input.split(" ", 1)[1]
                if os.path.exists(file_path):
                    await client.send_file(peer_entity, file_path)
                    console.print(f"[outgoing][{get_formatted_time()}] You: [Photo sent][/outgoing]")
                else:
                    console.print(f"[error]File not found: {file_path}[/error]")
            except IndexError:
                console.print("[error]Usage: /photo <file_path>[/error]")
            continue

        elif user_input.lower() == "/help":
            show_help()
            continue

        message_to_send = encode_to_c_code(user_input) if is_code_mode else user_input
        await client.send_message(peer_entity, message_to_send)
        console.print(f"[outgoing][{get_formatted_time()}] You: {user_input}[/outgoing]")

async def handle_new_message(event):
    """Event handler for new incoming messages."""
    global current_peer_entity, client
    
    sender = await event.get_sender()
    sender_name = sender.first_name if isinstance(sender, User) else event.chat.title if isinstance(event.chat, (Channel, Chat)) else 'Unknown'
    
    # Format message for either active chat or notification
    if current_peer_entity and event.is_private and event.chat_id == current_peer_entity.id:
        await event.message.mark_read()
        formatted_message = Text.from_markup(
            f"[timestamp][{get_formatted_time()}] [/timestamp][incoming]{sender_name}:[/incoming] {event.message.text}"
        )
    else:
        # This is a notification from a different chat
        formatted_message = Text.from_markup(
            f"[notification]NOTIFICATION from {sender_name}:[/notification] {event.message.text}"
        )
    
    console.print(formatted_message)

async def main():
    global client
    
    session = PromptSession(
        lexer=None, # Keep this as None for plain text input
        completer=WordCompleter(['/chat', '/exit', '/help'], ignore_case=True),
        complete_while_typing=True
    )
    
    with patch_stdout(raw=True):
        client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        await client.start()
        client.add_event_handler(handle_new_message, events.NewMessage)

        console.print("[info]Logged in successfully![/info]")
        console.print("Type /chat <username or phone> to start a chat. /exit to quit.\n")

        while True:
            try:
                user_input = await session.prompt_async("[prompt]TG> ")
            except (EOFError, KeyboardInterrupt):
                break
                
            user_input = user_input.strip()

            if not user_input:
                continue
            if user_input.lower() == "/exit":
                break
            if user_input.lower() == "/help":
                show_help()
                continue
            if user_input.lower().startswith("/chat"):
                try:
                    target = user_input.split(" ", 1)[1]
                    peer = await client.get_entity(target)
                    if isinstance(peer, User):
                        await chat_with_peer(peer, session)
                    else:
                        console.print("[error]That’s not a valid user.[/error]")
                except Exception as e:
                    console.print(f"[error]Failed to open chat: {e}[/error]")

        await client.disconnect()
        console.print("[info]Client disconnected.[/info]")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("[info]\nClient shut down by user.[/info]")
