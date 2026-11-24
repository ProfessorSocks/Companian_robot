### To start file (CD to root - cd ~/Documents/AI/Companian_Robot)
python3 -m brain.dev.coder_tool_test

### to start webserver go to /brain
source .venv/bin/activate

uvicorn brain.web.app:app --host 0.0.0.0 --port 8765


### to start ai hat 
hailo-ollama

### Hailo kill processes
sudo pkill -9 -f hailo-ollama

### Check active Processes
ps aux | grep -i hailo


### check and then kill specfic processes
pgrep -af hailo

sudo kill -9 PID