run:
	ngrok http 8001 &
	venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001
