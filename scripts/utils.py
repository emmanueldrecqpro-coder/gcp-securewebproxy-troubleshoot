import sys


# --- Color Codes for better terminal output ---
class Colors:
    """ANSI color codes for terminal output."""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_step(text):
    """Prints a formatted header."""
    print(f"\n{Colors.HEADER} {'*'*20} {text} {'*'*20} {Colors.ENDC}")


def print_header(text):
    """Prints a formatted header."""
    print(f"\n{Colors.HEADER}--- {text} ---{Colors.ENDC}")


def print_check(text, end="\n"):
    """Prints a check message."""
    print(f"{Colors.OKBLUE}➤ {text}...{Colors.ENDC}", end=end)


def print_success(text):
    """Prints a success message."""
    print(f"  {Colors.OKGREEN}✓ SUCCESS:{Colors.ENDC} {text}")


def print_fail(text, fatal=False):
    """Prints a failure message and optionally exits."""
    print(f"  {Colors.FAIL}✗ FAIL:{Colors.ENDC} {text}")
    if fatal:
        print(f"{Colors.FAIL}Aborting due to critical error.{Colors.ENDC}")
        sys.exit(1)
