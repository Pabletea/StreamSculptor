from fastapi import FastAPI, UploadFile, File
import whisper
import uvicorn
from pathlib import Path

app = FastAPI(title="Whisper Service")

# Cargar modelo (CPU, base para no consumir demasiado)
model = whisper.load_model("base")

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    temp_path = Path("/tmp") / file.filename
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    result = model.transcribe(str(temp_path))
    return {"segments": result["segments"], "text": result["text"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
