"""File watcher for monitoring ERP exports and triggering analysis."""
import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent


logger = logging.getLogger(__name__)


class ERPFileHandler(FileSystemEventHandler):
    """Handler for monitoring ERP export files."""

    def __init__(self, pattern: str = "*.xml", callback=None):
        """
        Initialize the ERP file handler.

        Args:
            pattern: File pattern to monitor (e.g., "*.xml", "balancete_*.xml")
            callback: Optional callable to execute when files are modified
        """
        self.pattern = pattern
        self.callback = callback

    def on_modified(self, event: FileModifiedEvent):
        """Handle file modification events."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if file_path.match(self.pattern):
            logger.info(f"Detected modified file: {file_path}")
            if self.callback:
                try:
                    self.callback(file_path)
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")

    def on_created(self, event: FileModifiedEvent):
        """Handle file creation events."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if file_path.match(self.pattern):
            logger.info(f"Detected new file: {file_path}")
            if self.callback:
                try:
                    self.callback(file_path)
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")


def watch_directory(
    directory: Path,
    pattern: str = "*.xml",
    callback=None,
    recursive: bool = True,
) -> Observer:
    """
    Watch a directory for file changes.

    Args:
        directory: Directory to watch
        pattern: File pattern to monitor
        callback: Callable to execute on file changes
        recursive: Whether to watch subdirectories

    Returns:
        Observer instance (not started)
    """
    handler = ERPFileHandler(pattern=pattern, callback=callback)
    observer = Observer()
    observer.schedule(handler, str(directory), recursive=recursive)
    return observer


def main():
    """Main entry point for file watcher."""
    parser = argparse.ArgumentParser(
        description="Monitor ERP export directory for changes"
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Directory to watch for ERP exports",
    )
    parser.add_argument(
        "--pattern",
        default="*.xml",
        help="File pattern to monitor (default: *.xml)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        default=True,
        help="Watch subdirectories (default: True)",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Validate directory
    if not args.directory.exists():
        logger.error(f"Directory does not exist: {args.directory}")
        return 1

    if not args.directory.is_dir():
        logger.error(f"Path is not a directory: {args.directory}")
        return 1

    logger.info(f"Starting file watcher on {args.directory}")
    logger.info(f"Pattern: {args.pattern}")

    # Simple callback that logs file changes
    def on_file_change(file_path: Path):
        logger.info(f"Processing file: {file_path}")

    # Watch directory
    observer = watch_directory(
        args.directory,
        pattern=args.pattern,
        callback=on_file_change,
        recursive=args.recursive,
    )

    observer.start()
    logger.info("File watcher is running (Ctrl+C to stop)")

    try:
        while True:
            observer.join(timeout=1)
    except KeyboardInterrupt:
        logger.info("Stopping file watcher...")
        observer.stop()

    observer.join()
    return 0


if __name__ == "__main__":
    sys.exit(main())
