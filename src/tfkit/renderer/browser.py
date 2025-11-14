from __future__ import annotations

import shutil
import time
import webbrowser
from pathlib import Path
from typing import Any, Callable, Literal, Self

BrowserType = Literal[
    "default", "chrome", "firefox", "safari", "edge", "opera", "windows-default"
]

CleanupStrategy = Literal["on_exit", "on_open", "manual"]


class Browser:
    """
    A service for opening a local resource in a specific browser and
    managing the controlled cleanup of associated files or directories
    via a context manager.
    """

    # ------------------------------------------------------------------ #
    # Constructor and Context Management
    # ------------------------------------------------------------------ #

    def __init__(
        self,
        resource_path: Path,
        cleanup_path: Path | None = None,
        preferred_browser: BrowserType = "default",
        cleanup_strategy: CleanupStrategy = "on_exit",
        delay_seconds: float = 1.0,
    ) -> None:
        """
        Initialize the Browser service.

        Args:
            resource_path: The local path to the resource file (e.g., HTML report).
            cleanup_path: An optional path (file or directory) to be deleted.
                          If None, no cleanup is performed.
            preferred_browser: The specific browser to try and use.
            cleanup_strategy: When the cleanup should occur:
                              'on_exit' (default, when context block finishes)
                              'on_open' (immediately after successful browser launch)
                              'manual' (requires calling .cleanup() explicitly)
            delay_seconds: A small delay after successful opening, useful before 'on_open' cleanup.
        """
        if not resource_path.is_file():
            raise FileNotFoundError(
                f"Resource to open not found or is not a file: {resource_path}"
            )

        self.resource_path = resource_path.resolve()
        self.cleanup_path = cleanup_path.resolve() if cleanup_path else None
        self.preferred_browser = preferred_browser
        self.cleanup_strategy = cleanup_strategy
        self.delay_seconds = delay_seconds
        self._webbrowser_instance: webbrowser.BaseBrowser | None = None

        if preferred_browser != "default":
            self._register_browser(preferred_browser)

    def __enter__(self) -> Self:
        """Enters the context."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Exits the context. Performs 'on_exit' cleanup if configured.
        """
        if self.cleanup_strategy == "on_exit":
            self._cleanup_resource()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def open(self) -> bool:
        """
        Open the instance's resource file in the configured browser.

        Returns:
            True if the browser launched successfully, False otherwise.
        """
        print("---")
        print(f"🌍 Opening local resource: **{self.resource_path.name}**")
        print(f"Preferred Browser: **{self.preferred_browser}**")
        print(f"Path: {self.resource_path}")

        url = f"file://{self.resource_path}"

        # Determine which browser opener to use
        opener: Callable[[str], bool]
        if self._webbrowser_instance:
            opener = self._webbrowser_instance.open
        else:
            opener = webbrowser.open  # Uses default or relies on system path

        success = opener(url)

        if success:
            print("Browser launched successfully.")
            self._print_security_tip()

            if self.cleanup_strategy == "on_open":
                time.sleep(self.delay_seconds)  # Give browser time to load file
                self._cleanup_resource()
        else:
            print("🚨 Could not launch browser automatically.")
            self._print_manual_open(url)

        print("---")
        return success

    def cleanup(self) -> None:
        """
        Manually trigger the resource cleanup. Useful when cleanup_strategy is 'manual'.
        """
        self._cleanup_resource()

    # ------------------------------------------------------------------ #
    # Private Methods
    # ------------------------------------------------------------------ #

    def _register_browser(self, browser_name: BrowserType) -> None:
        """
        Attempts to register and get the specified browser instance.
        """
        try:
            self._webbrowser_instance = webbrowser.get(browser_name)
        except webbrowser.Error as e:
            print(
                f"⚠️ Warning: Could not find '{browser_name}' opener. Falling back to default browser."
            )
            print(f"  Details: {e}")
            self._webbrowser_instance = None
            self.preferred_browser = "default"

    def _cleanup_resource(self) -> None:
        """
        Safely attempts to remove the file or directory specified by cleanup_path.
        """
        path_to_clean = self.cleanup_path

        if not path_to_clean or not path_to_clean.exists():
            return

        print("---")
        print(
            f"🧹 Starting cleanup for: {path_to_clean.name} (Strategy: {self.cleanup_strategy})"
        )

        try:
            if path_to_clean.is_file():
                path_to_clean.unlink()
                print(f"File cleaned up: {path_to_clean.name}")
            elif path_to_clean.is_dir():
                shutil.rmtree(path_to_clean)
                print(f"Directory cleaned up: {path_to_clean.name}")
            else:
                print(
                    f"Cleanup skipped: {path_to_clean.name} is not a file or directory."
                )
        except OSError as e:
            print(
                f"⚠️ Error during cleanup of {path_to_clean.name}. It might be locked by the browser."
            )
            print(f"  Details: {e}")
        finally:
            print("---")

    @staticmethod
    def _print_security_tip() -> None:
        """Prints a tip about local file security warnings."""
        print(
            "> Note: The browser may show security warnings - this is normal "
            "for local ``file://`` URLs (e.g., restricted JavaScript/CSS or "
            "cross-origin access issues). This is a browser security measure."
        )

    @staticmethod
    def _print_manual_open(url: str) -> None:
        """Prints instructions for manually opening the file."""
        print(
            "Manual opening required. Please copy and paste this URL into your browser:"
        )
        print(f"   **{url}**")
