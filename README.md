# Modly LocalMesh four-view adapter (prototype)

This adapter uses Modly's front Image node plus three explicit file paths. It requires an existing, working LocalMesh Engine installation. It does not install model weights, CUDA extensions, or bypass DINOv3 access. Tested structurally only; no Modly desktop or NVIDIA GPU is available in this workspace.

## Setup on Windows

1. Install LocalMesh Engine and its four-view dependencies from https://github.com/Quentincls/localmesh-engine/blob/main/docs/INSTALL.md . First confirm its official four-view CLI runs on your computer.
2. Place this directory in your Modly extensions/plugin folder if you manage extensions manually. Modly's supported *Install from GitHub* flow requires these files at the root of a GitHub repository; a local folder alone is not an Install from GitHub URL.
3. In Modly Workflows, connect Image (front) → LocalMesh Four View → Add to Scene.
4. Enter full Windows file paths for right, left and back. The Python executable field may be left blank: the adapter checks `LOCALMESH_PYTHON`, `LOCALMESH_ROOT`, and common locations such as `C:\\localmesh-engine\\.venv\\Scripts\\python.exe`, Desktop, Documents, and OneDrive\\Documents. If LocalMesh is elsewhere, paste its `.venv\\Scripts\\python.exe` path or set one of those variables. Some Modly versions open a directory picker for string parameters, so typing/pasting is more reliable.
5. Choose Standard first; the output is a GLB. For an STL, inspect and repair the mesh and scale it in Blender before export.

This plugin deliberately uses a separate LocalMesh Python environment to avoid conflicting with Modly's PyTorch installation. Modly's extension installer may require extra setup/download metadata for your release; manual folder placement and restart are version-dependent. Do not treat structural checks as proof of a working installation.
