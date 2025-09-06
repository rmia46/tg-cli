# This file contains various code templates for different programming languages.
# The templates are designed to embed a user's message into a function's output.

CODE_TEMPLATES = {
    "c": [
        # C Template 1: Basic function to print message
        """#include <stdio.h>
#include <string.h>

void printMessage(const char* msg) {{
    printf("%s\\n", msg);
}}

int main() {{
    printMessage("{{message}}");
    return 0;
}}
""",
        # C Template 2: Function with a simple loop
        """#include <stdio.h>
#include <string.h>

void echoMessage(const char* msg) {{
    for (int i = 0; i < strlen(msg); i++) {{
        printf("%c", msg[i]);
    }}
    printf("\\n");
}}

int main() {{
    echoMessage("{{message}}");
    return 0;
}}
""",
        # C Template 3: Function to print message and length
        """#include <stdio.h>
#include <string.h>

void reportStatus(const char* status) {{
    printf("Status report: %s\\n", status);
    printf("Message length: %d bytes\\n", (int)strlen(status));
}}

int main() {{
    reportStatus("{{message}}");
    return 0;
}}
"""
    ],
    "cpp": [
        # C++ Template 1: Basic function with std::cout
        """#include <iostream>
#include <string>

void displayMessage(const std::string& msg) {{
    std::cout << msg << std::endl;
}}

int main() {{
    displayMessage("{{message}}");
    return 0;
}}
""",
        # C++ Template 2: Class-based approach
        """#include <iostream>
#include <string>

class ConsoleMessenger {{
public:
    void log(const std::string& msg) {{
        std::cout << "LOG: " << msg << std::endl;
    }}
}};

int main() {{
    ConsoleMessenger messenger;
    messenger.log("{{message}}");
    return 0;
}}
"""
    ],
    "java": [
        # Java Template 1: Simple class with main method
        """class MyProgram {{
    public static void main(String[] args) {{
        System.out.println("{{message}}");
    }}
}}
""",
        # Java Template 2: Method-based approach
        """class MessageHandler {{
    public void processMessage(String message) {{
        System.out.println("Processing message: " + message);
    }}
}}

public class Main {{
    public static void main(String[] args) {{
        MessageHandler handler = new MessageHandler();
        handler.processMessage("{{message}}");
    }}
}}
"""
    ],
    "python": [
        # Python Template 1: Simple print statement
        """import sys

def output_message(msg):
    print(msg)

if __name__ == "__main__":
    output_message("{{message}}")
""",
        # Python Template 2: Simple class
        """class MessageProcessor:
    def __init__(self, message):
        self.message = message
    
    def display(self):
        print(f"Message: {{self.message}}")

if __name__ == "__main__":
    processor = MessageProcessor("{{message}}")
    processor.display()
"""
    ]
}
