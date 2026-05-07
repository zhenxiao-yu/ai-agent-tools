# Future Tray Launcher Notes

The current safe launcher uses normal Windows shortcuts and PowerShell scripts.

A future tray launcher could be built as a tiny local app that:

- starts or opens `http://127.0.0.1:8501`
- shows dashboard running/stopped status
- opens logs and reports folders
- never stores API keys
- never starts scheduled repo workers automatically

Do not install heavy tray utilities or background launchers without approval. The shortcut approach is simpler and safer for now.
