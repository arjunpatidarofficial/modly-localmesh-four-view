"""Modly adapter for an existing LocalMesh Engine Python installation."""
import subprocess
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Callable, Optional

from services.generators.base import BaseGenerator, GenerationCancelled


class LocalMeshFourViewGenerator(BaseGenerator):
    MODEL_ID = "localmesh-four-view"
    DISPLAY_NAME = "LocalMesh Four View"
    VRAM_GB = 8
    IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
    TIERS = {"draft", "standard", "high"}

    def is_downloaded(self) -> bool:
        # Weights and runtime are managed by LocalMesh, outside Modly.
        return True

    def load(self) -> None:
        pass

    def generate(self, image_bytes: bytes, params: dict,
                 progress_cb: Optional[Callable[[int, str], None]] = None,
                 cancel_event: Optional[threading.Event] = None) -> Path:
        views = {}
        for role in ("right", "left", "back"):
            value = str(params.get(f"{role}_image_path", "")).strip().strip('"')
            path = Path(value).expanduser()
            if not value or not path.is_file() or path.suffix.lower() not in self.IMAGE_SUFFIXES:
                raise ValueError(f"Valid {role} image path required (PNG/JPEG/WebP): {value}")
            views[role] = path.resolve()
        python = str(params.get("python_exe", "")).strip().strip('"')
        python_path = Path(python).expanduser()
        if not python or not python_path.is_file():
            raise ValueError("Set python_exe to LocalMesh's .venv\\Scripts\\python.exe")
        tier = str(params.get("tier", "standard"))
        if tier not in self.TIERS:
            raise ValueError("Four-view tier must be draft, standard or high")
        try:
            seed = int(params.get("seed", -1))
        except (TypeError, ValueError) as exc:
            raise ValueError("Seed must be an integer between -1 and 4294967295") from exc
        if not -1 <= seed <= 4294967295:
            raise ValueError("Seed must be between -1 and 4294967295")
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="modly-localmesh-") as directory:
            front = Path(directory) / "front.png"
            front.write_bytes(image_bytes)
            output = Path(directory) / "result"
            command = [str(python_path), "-m", "localmesh_engine", str(front),
                       "--right", str(views["right"]), "--left", str(views["left"]),
                       "--back", str(views["back"]), "--tier", tier,
                       "--seed", str(seed), "--to", str(output)]
            if progress_cb:
                progress_cb(5, "Starting LocalMesh Engine")
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       text=True, errors="replace", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            started = time.monotonic()
            try:
                while process.poll() is None:
                    if cancel_event is not None and cancel_event.is_set():
                        process.terminate()
                        try:
                            process.wait(timeout=8)
                        except subprocess.TimeoutExpired:
                            process.kill()
                        raise GenerationCancelled("LocalMesh generation cancelled")
                    if progress_cb:
                        progress_cb(min(90, 10 + int((time.monotonic() - started) / 15)), "Generating four-view mesh")
                    time.sleep(0.5)
                stdout, stderr = process.communicate()
                if process.returncode != 0:
                    raise RuntimeError(f"LocalMesh failed ({process.returncode}): {stderr[-2500:]}")
                candidates = sorted(
                    (p for p in output.rglob("*.glb") if p.is_file() and p.stat().st_size > 0),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True,
                ) if output.is_dir() else []
                if not candidates:
                    raise RuntimeError(f"LocalMesh produced no GLB. Output: {stdout[-1000:]} {stderr[-1000:]}")
                destination = self.outputs_dir / f"localmesh_{int(time.time())}_{uuid.uuid4().hex[:8]}.glb"
                destination.write_bytes(candidates[0].read_bytes())
                if progress_cb:
                    progress_cb(100, "GLB ready")
                return destination
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
