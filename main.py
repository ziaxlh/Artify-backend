from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import requests
import os
import io

API_KEY = 'yrQwKj6H2UjwAXynVD8eEqcv'

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "static/uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload-image/")
async def upload_image(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())
    return {"file_path": file_path}

@app.post("/remove-background/")
async def remove_background(file: UploadFile = File(...)):
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only jpg and png are allowed.")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    try:
        response = requests.post(
            'https://api.remove.bg/v1.0/removebg',
            files={'image_file': open(file_path, 'rb')},
            data={'size': 'auto'},
            headers={'X-Api-Key': API_KEY},
        )
        if response.status_code == requests.codes.ok:
            output_path = file_path.replace(".", "_no_bg.")
            with open(output_path, 'wb') as out:
                out.write(response.content)
            return {"output_path": output_path}
        else:
            return {"error": response.json()}
    except Exception as e:
        return {"error": str(e)}

@app.post("/change-format/")
async def change_image_format(file: UploadFile = File(...), format: str = Form(...)):
    if file.content_type not in ["image/jpeg", "image/png", "image/gif", "image/bmp"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only jpg, png, bmp, and gif are allowed.")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    try:
        image = Image.open(file_path)
        new_format = format.lower()
        new_file_path = file_path.replace(file.filename.split('.')[-1], new_format)
        
        if new_format == 'jpg' and image.mode == 'RGBA':
            image = image.convert('RGB')

        image.save(new_file_path)
        return {"new_file_path": new_file_path}
    except Exception as e:
        return {"error": str(e)}

@app.get("/download/")
async def download_file(file_path: str):
    return FileResponse(file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
