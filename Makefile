# Makefile

VENV    := venv
PYTHON  := $(VENV)/Scripts/python.exe

.PHONY: install server tui peer start clean

install: clean
	python -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt
	@echo "Activate your venv with:"
	@echo "  source $(VENV)/Scripts/activate"

server:
	@echo "Starting discovery server on http://127.0.0.1:8000"
	$(PYTHON) -m uvicorn discovery_server.main:app \
		--reload --host 127.0.0.1 --port 8000

tui:
	@echo "Starting Textual UI client"
	$(PYTHON) tui.py

peer:
	@echo "Starting CLI peer client"
	$(PYTHON) peer_client.py

clean:
	rm -rf $(VENV)
	rm -f tui_debug.log
