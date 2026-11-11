$ErrorActionPreference = "Stop"

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m PyInstaller --noconfirm --clean --windowed --name "DM-Ticket-Assistant" --paths "src" "src/dm_ticket_assistant/__main__.py"

Write-Host "Build completed: dist/DM-Ticket-Assistant/"
