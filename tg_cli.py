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
import random
import base64
from telethon import TelegramClient, events
from telethon.tl.types import User, Channel, Chat
from rich.console import Console
from rich.theme import Theme
from rich.text import Text
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax
from datetime import datetime
from dotenv import load_dotenv
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.completion import Completer, Completion
from code_templates import CODE_TEMPLATES
from emoji_map import EMOJI_MAP

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
    "notification": "yellow",
    "matrix_panel": "bold green on black",
    "welcome_gradient": "bold rgb(0,255,0) on black",
    "prompt_static": "bold green",
    "prompt_dynamic": "bold cyan",
})

# Initialize the Rich Console with the custom theme
console = Console(theme=cli_theme)

# Session name for persistent login
SESSION_NAME = 'cli_session'

# Global state variables for the chat session and display
current_peer_entity = None
is_code_mode = False
is_cloak_mode = False
current_language = "c" # Default language is C
client = None

# ==================== UTILITY FUNCTIONS ====================

def clear_screen():
    """Clears the console screen."""
    console.clear()

def get_formatted_time():
    """Returns the current timestamp in HH:MM:SS format."""
    return datetime.now().strftime('%H:%M:%S')

def emojify_message(message):
    """Replaces text codes with emojis."""
    for code, emoji in EMOJI_MAP.items():
        message = message.replace(code, emoji)
    return message

def cloak_message(message):
    """Encodes a message for display in cloak mode."""
    # A simple, reversible encoding.
    encoded_bytes = base64.b64encode(message.encode('utf-8'))
    return f"[dim white]Encoded Phrase: {encoded_bytes.decode('utf-8')}[/dim white]"

def encode_message(message, lang):
    """
    Encodes a message into a randomized code template for a given language.
    The message is passed to a function within the code.
    """
    if lang not in CODE_TEMPLATES:
        return f"```\nError: No templates found for language '{lang}'.\n```"

    
    # Get a random template for the selected language
    selected_template = random.choice(CODE_TEMPLATES[lang])
    
    # Escape characters based on the language
    if lang in ["c", "cpp"]:
        escaped_message = message.replace('"', '\\"')
    elif lang == "java":
        escaped_message = message.replace('"', '\\"').replace('\\', '\\\\')
    else: # For python and others, minimal escaping is needed
        escaped_message = message
        
    # Replace the placeholder with the escaped message
    formatted_code = selected_template.replace("{{message}}", escaped_message)
    
    # Wrap the code in markdown for nice formatting
    return f"```{lang}\n{formatted_code}\n```"

def show_help():
    """Prints the list of available commands."""
    console.print("\n[bold]Available Commands:[/bold]")
    console.print("  [yellow]/chat <username/phone>[/yellow] - Start a new chat session.")
    console.print("  [yellow]/togglecode[/yellow] - Toggle code encoding mode.")
    console.print("  [yellow]/togglecloak[/yellow] - Toggle cloak mode for your messages.")
    console.print("  [yellow]/lang <c|cpp|java|python>[/yellow] - Change the encoding language.")
    console.print("  [yellow]/photo <file_path>[/yellow] - Send a photo from a file.")
    console.print("  [yellow]/back[/yellow] - Return to peer selection from an active chat.")
    console.print("  [yellow]/help[/yellow] - Show this help message.")
    console.print("  [yellow]/exit[/yellow] - Log out and exit the client.")
    console.print("  [yellow]Emoji Shortcuts[/yellow] - Type text codes (e.g., :smile:, :heart:) to convert to emojis.")
    console.print("\n[info]Messages from other chats will appear as notifications.[/info]")
    console.print(f"[info]Current language: {current_language.upper()}[/info]")

# ==================== PROMPT-TOOLKIT CLASSES ====================

class DynamicCompleter(Completer):
    """
    Provides context-aware auto-completion.
    """
    def get_completions(self, document, complete_event):
        text_before_cursor = document.text_before_cursor.lstrip()
        words = text_before_cursor.split()
        
        # Command completion
        if text_before_cursor.startswith('/') and len(words) == 1:
            commands = ['/chat', '/togglecode', '/togglecloak', '/lang', '/photo', '/back', '/help', '/exit']
            for cmd in commands:
                if cmd.startswith(text_before_cursor):
                    yield Completion(cmd, start_position=-len(text_before_cursor))
        
        # Language completion after /lang
        elif text_before_cursor.startswith('/lang') and len(words) == 2:
            current_word = words[-1]
            for lang in CODE_TEMPLATES.keys():
                if lang.startswith(current_word):
                    yield Completion(lang, start_position=-len(current_word))
                    
        # Emoji completion
        elif ':' in text_before_cursor:
            current_word = text_before_cursor.split()[-1]
            if current_word.startswith(':'):
                for emoji_code in EMOJI_MAP.keys():
                    if emoji_code.startswith(current_word):
                        # The display text shows the emoji next to the code
                        display_text = f"{emoji_code} {EMOJI_MAP[emoji_code]}"
                        yield Completion(
                            emoji_code,
                            start_position=-len(current_word),
                            display=display_text
                        )
        
# ==================== MAIN LOGIC FUNCTIONS ====================

async def chat_with_peer(peer_entity, session):
    """Manages the interactive chat session with a specific peer."""
    global is_code_mode, is_cloak_mode, current_peer_entity, current_language
    
    current_peer_entity = peer_entity
    peer_name = getattr(peer_entity, "first_name", None) or "Unknown"
    
    # Fancy panel for starting chat session
    panel_title = f"[bold green]Session with: {peer_name}[/bold green]"
    panel_content = Text.from_markup("[info]Commands: /back, /togglecode, /togglecloak, /lang, /photo, /help[/info]\n")
    chat_panel = Panel(panel_content, title=panel_title, border_style="matrix_panel")
    console.print(chat_panel)

    while True:
        try:
            user_input = await session.prompt_async("[prompt]> ")
        except (EOFError, KeyboardInterrupt):
            current_peer_entity = None
            console.print(f"\n[info]Exiting chat session with {peer_name}.[/info]\n")
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
            console.print(f"[info]Code mode {status}. Current language: {current_language.upper()}[/info]")
            continue
            
        elif user_input.lower() == "/togglecloak":
            is_cloak_mode = not is_cloak_mode
            status = "ON" if is_cloak_mode else "OFF"
            console.print(f"[info]Cloak mode {status}.[/info]")
            continue

        elif user_input.lower().startswith("/lang"):
            try:
                lang = user_input.split(" ", 1)[1].lower()
                if lang in CODE_TEMPLATES:
                    current_language = lang
                    console.print(f"[info]Language set to {lang.upper()}[/info]")
                else:
                    console.print(f"[error]Unsupported language: {lang}. Supported languages are: {', '.join(CODE_TEMPLATES.keys())}[/error]")
            except IndexError:
                console.print("[error]Usage: /lang <c|cpp|java|python>[/error]")
            continue

        elif user_input.lower().startswith("/photo"):
            try:
                file_path = user_input.split(" ", 1)[1]
                if os.path.exists(file_path):
                    await client.send_file(peer_entity, file_path)
                    console.print(f"[outgoing][{get_formatted_time()}] Yu: [Photo sent][/outgoing]")
                else:
                    console.print(f"[error]File not found: {file_path}[/error]")
            except IndexError:
                console.print("[error]Usage: /photo <file_path>[/error]")
            continue

        elif user_input.lower() == "/help":
            show_help()
            continue

        # Autocorrect emojis before sending the message
        emojified_input = emojify_message(user_input)
        
        # Determine the message to send and the message to display locally
        message_to_send = emojified_input
        
        if is_code_mode and is_cloak_mode:
            # When both modes are active, send the code but only show "Delivered" locally
            message_to_send = encode_message(emojified_input, current_language)
            console.print(f"[outgoing][{get_formatted_time()}] Yu: [Delivered][/outgoing]")
        elif is_code_mode:
            # If only code mode is active, send the code and display it locally
            message_to_send = encode_message(emojified_input, current_language)
            encoded_syntax = Syntax(message_to_send, current_language, theme="monokai", word_wrap=True)
            console.print(f"[outgoing][{get_formatted_time()}] Yu: [/outgoing]", encoded_syntax)
        elif is_cloak_mode:
            # If only cloak mode is active, send the plain message and display it encoded
            cloaked_message = cloak_message(emojified_input)
            console.print(f"[outgoing][{get_formatted_time()}] Yu: {cloaked_message}[/outgoing]")
        else:
            # If neither mode is active, send and display the plain message
            console.print(f"[outgoing][{get_formatted_time()}] Yu: {emojified_input}[/outgoing]")
            
        await client.send_message(peer_entity, message_to_send)

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
    # Correctly declare global variables to modify them inside this function
    global client, current_language, is_code_mode, is_cloak_mode

    # --- NEW LOGIC FOR .ENV FILE CREATION ---
    if not os.path.exists(".env"):
        panel_content = Text.from_markup(
            "[bold red]Configuration Required![/bold red]\n\n"
            "This application needs your Telegram API credentials. You'll need to create a .env file.\n"
            "Go to [link=https://my.telegram.org]my.telegram.org[/link] to get your API ID and API Hash.\n\n"
            "Please enter your credentials below:"
        )
        console.print(Panel(panel_content, title="⚠️ Initial Setup", border_style="bold red"))
        
        try:
            api_id = input("Enter your API_ID: ").strip()
            api_hash = input("Enter your API_HASH: ").strip()
            
            with open(".env", "w") as f:
                f.write(f"API_ID={api_id}\n")
                f.write(f"API_HASH={api_hash}\n")
            
            console.print("[info]Successfully created .env file![/info]")
            # Reload environment variables from the new file
            load_dotenv()
        except Exception as e:
            console.print(f"[error]Failed to create .env file: {e}[/error]")
            sys.exit(1)
            
    # Load API keys from the .env file
    API_ID = int(os.getenv('API_ID', '0'))
    API_HASH = os.getenv('API_HASH', '')

    # Check if the API keys are valid after the file has been created and reloaded
    if not API_ID or not API_HASH or API_ID == 0:
        console.print(Panel(
            "[bold red]API credentials are still missing or invalid.[/bold red]\n"
            "Please check the .env file and try again.",
            title="⚠️ Error",
            border_style="bold red"
        ))
        sys.exit(1)
    # --- END OF NEW LOGIC ---

    completer = DynamicCompleter()
    session = PromptSession(
        lexer=None, # Keep this as None for plain text input
        completer=completer,
        complete_while_typing=True,
    )
    
    # Wrap the entire main logic in a try...finally block
    # to ensure the client is always disconnected
    try:
        with patch_stdout(raw=True):
            client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
            await client.start()
            client.add_event_handler(handle_new_message, events.NewMessage)

            # Fancy welcome message
            welcome_text = Text("Welcome to the CLI Telegram Client", style="welcome_gradient")
            console.print(Panel(welcome_text, title="🟢 🟢 🟢", title_align="right", border_style="matrix_panel"))
            console.print(Rule(style="matrix_panel"))
            
            console.print("[info]Logged in successfully![/info]")
            console.print("Type /chat <username or phone> to start a chat. /exit to quit.\n")

            while True:
                try:
                    # The prompt is now a rich.Text object
                    prompt_text = Text()
                    prompt_text.append(f"TG ({current_language.upper()})", style="prompt_static")
                    # Dynamically add status indicators to the prompt
                    if is_code_mode:
                        prompt_text.append(" [CODE]", style="bold green")
                    if is_cloak_mode:
                        prompt_text.append(" [CLOAK]", style="bold magenta")
                    prompt_text.append(" > ", style="prompt_dynamic")
                    user_input = await session.prompt_async(prompt_text.plain)
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
                elif user_input.lower().startswith("/lang"):
                    try:
                        lang = user_input.split(" ", 1)[1].lower()
                        if lang in CODE_TEMPLATES:
                            current_language = lang
                            console.print(f"[info]Language set to {lang.upper()}[/info]")
                        else:
                            console.print(f"[error]Unsupported language: {lang}. Supported languages are: {', '.join(CODE_TEMPLATES.keys())}[/error]")
                    except IndexError:
                        console.print("[error]Usage: /lang <c|cpp|java|python>[/error]")
                    continue
                elif user_input.lower() == "/togglecode":
                    is_code_mode = not is_code_mode
                    status = "ON" if is_code_mode else "OFF"
                    console.print(f"[info]Code mode {status}. Current language: {current_language.upper()}[/info]")
                    continue
                elif user_input.lower() == "/togglecloak":
                    is_cloak_mode = not is_cloak_mode
                    status = "ON" if is_cloak_mode else "OFF"
                    console.print(f"[info]Cloak mode {status}.[/info]")
                    continue
                else:
                    console.print("[error]Invalid command. Type /help to see all commands.[/error]")
    
    finally:
        # This block ensures the client disconnects gracefully,
        # releasing the lock on the session filea
        if client:
            await client.disconnect()
            console.print("[info]Client disconnected.[/info]")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("[info]\nClient shut down by user.[/info]")
