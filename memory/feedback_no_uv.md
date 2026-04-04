---
name: No uv - use pip
description: User says uv doesn't work on their machine; use pip and venv instead
type: feedback
---

Do not use `uv` for Python environment/package management — it doesn't work on this user's machine.

**Why:** User reported uv is broken on their computer.
**How to apply:** Use `python3 -m venv` for virtual environments and `pip` for package installs.
