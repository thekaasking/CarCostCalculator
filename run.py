"""Main entry point for the application.

Separates the application from the main entry point,
mostly to fix relative imports when running the application.
"""

from src.app import main


if __name__ == "__main__":
    main()
