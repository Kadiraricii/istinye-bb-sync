#!/usr/bin/env python3
"""Auto-restart dev runner: watches .py files and restarts the app on change."""
import subprocess
import sys
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

DEBOUNCE = 1.2  # saniye — IDE bazen tek kayıtta 3-4 event ateşler


class RestartHandler(FileSystemEventHandler):
    def __init__(self) -> None:
        self.process: subprocess.Popen | None = None
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()
        self._start()

    def _start(self) -> None:
        with self._lock:
            if self.process and self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            print("\n▶  Starting app...\n")
            self.process = subprocess.Popen([sys.executable, "main.py"])

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        if not str(event.src_path).endswith(".py"):
            return
        # Debounce: birden fazla rapid event gelirse sadece son birini işle
        with self._lock:
            if self._timer:
                self._timer.cancel()
            name = Path(event.src_path).name
            self._timer = threading.Timer(DEBOUNCE, self._delayed_restart, args=(name,))
            self._timer.start()

    def _delayed_restart(self, filename: str) -> None:
        print(f"\n↻  Changed: {filename} — restarting...")
        self._start()

    def stop(self) -> None:
        with self._lock:
            if self._timer:
                self._timer.cancel()
            if self.process and self.process.poll() is None:
                self.process.terminate()


if __name__ == "__main__":
    handler = RestartHandler()
    observer = Observer()
    observer.schedule(handler, path=".", recursive=True)
    observer.start()
    print("👁  Watching for changes (Ctrl+C to stop)...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        handler.stop()
    observer.join()
