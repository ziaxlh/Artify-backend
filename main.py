from fastapi import FastAPI
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from PIL import Image
import requests
import io
from fastapi.middleware.cors import CORSMiddleware

API_KEY = 'yrQwKj6H2UjwAXynVD8eEqcv'

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Agrega la URL de tu aplicaci贸n de React
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.post("/remove-background")
async def remove_background(file: UploadFile = File(...)):
    try:
        print("Solicitud recibida en /remove-background")
        input_image = await file.read()
        response = requests.post('https://api.remove.bg/v1.0/removebg',
        files={'image_file': input_image},
        data={'size': 'auto'},
        headers={'X-Api-Key': API_KEY},
        )
        if response.status_code == requests.codes.ok:
            return FileResponse(io.BytesIO(response.content), media_type="image/png", filename="output.png")
        else:
            return JSONResponse(content={"error": response.text}, status_code=response.status_code)
    except Exception as e:
        print(f"Error al procesar la solicitud en /remove-background: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/hola")
async def remove_background(file: UploadFile = File(...)):
    try:
        print("hola")
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/change-format")
async def change_image_format(file: UploadFile = File(...), format: str = "png"):
    try:
        input_image = await file.read()
        image = Image.open(io.BytesIO(input_image))
        output = io.BytesIO()
        
        if format.lower() not in ["jpeg", "png", "bmp", "gif"]:
            return JSONResponse(content={"error": "Formato no soportado"}, status_code=400)
        
        if image.mode == 'RGBA' and format.lower() == "jpeg":
            image = image.convert('RGB')
        
        image.save(output, format=format.upper())
        output.seek(0)
        
        return FileResponse(output, media_type=f"image/{format}", filename=f"output.{format}")
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)