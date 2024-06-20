from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageEnhance, ImageFilter, UnidentifiedImageError
import requests
import os
import logging
from io import BytesIO
from fastapi.responses import StreamingResponse

API_KEY = 'dA8dubQCxH3jKZFG5AY6pS6y'

app = FastAPI()

# Configuración para permitir CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Reemplaza con tu dominio de frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración para servir archivos estáticos
UPLOAD_DIR = "static/uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Rutas de API

@app.post("/upload-image/")
async def upload_image(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())
    normalized_path = file_path.replace("\\", "/")
    return {"file_path": normalized_path}

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
            normalized_output_path = output_path.replace("\\", "/")
            return {"output_path": normalized_output_path}
        else:
            error_response = response.json()
            return JSONResponse(status_code=400, content={"error": error_response.get('errors', [{'title': 'Unknown error'}])[0]['title']})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/change-format/")
async def change_image_format(file: UploadFile = File(...), format: str = Form(...)):
    try:
        if file.content_type not in ["image/jpeg", "image/png", "image/gif", "image/bmp", "image/jpg"]:
            raise HTTPException(status_code=400, detail="Invalid file type. Only jpg, png, bmp y gif.")

        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())

        image = Image.open(file_path)
        new_format = format.lower()
        new_file_path = f"{os.path.splitext(file_path)[0]}.{new_format}"

        if new_format == 'jpg' and image.mode == 'RGBA':
            image = image.convert('RGB')

        image.save(new_file_path)

        normalized_new_file_path = new_file_path.replace("\\", "/")
        return {"new_file_path": normalized_new_file_path}

    except UnidentifiedImageError:
        logging.error(f"Error al procesar la imagen: No se puede identificar el archivo de imagen '{file_path}'")
        return JSONResponse(status_code=400, content={"error": "No se puede identificar el archivo de imagen."})
    
    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        logging.error(f"Error al procesar la imagen: {str(e)}")
        return JSONResponse(status_code=500, content={"error": "Error interno del servidor."})

@app.post("/convert-image/")
async def convert_image(file: UploadFile = File(...), format: str = Form(...)):
    return await change_image_format(file, format)

@app.post("/apply-filter/")
async def apply_filter(file: UploadFile = File(...), filter_name: str = Form(...)):
    if file.content_type not in ["image/jpeg", "image/png", "image/gif", "image/bmp"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only jpg, png, bmp y gif.")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    try:
        image = Image.open(file_path)
        if filter_name == "BLUR":
            image = image.filter(ImageFilter.BLUR)
        elif filter_name == "CONTOUR":
            image = image.filter(ImageFilter.CONTOUR)
        elif filter_name == "DETAIL":
            image = image.filter(ImageFilter.DETAIL)
        elif filter_name == "EDGE_ENHANCE":
            image = image.filter(ImageFilter.EDGE_ENHANCE)
        elif filter_name == "SHARPEN":
            image = image.filter(ImageFilter.SHARPEN)
        elif filter_name == "SMOOTH":
            image = image.filter(ImageFilter.SMOOTH)
        elif filter_name == "BRIGHTNESS":
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.5)
        elif filter_name == "CONTRAST":
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
        else:
            raise HTTPException(status_code=400, detail="Invalid filter name.")

        filtered_file_path = file_path.replace(".", f"_{filter_name.lower()}.")
        image.save(filtered_file_path)
        normalized_filtered_file_path = filtered_file_path.replace("\\", "/")
        return {"filtered_file_path": normalized_filtered_file_path}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/convert/")
async def convert_image(file: UploadFile = File(...), format: str = "png"):
    try:
        contents = await file.read()
        image = Image.open(BytesIO(contents))
        
        # Crear un buffer para almacenar la imagen convertida
        output = BytesIO()
        image.save(output, format=format.upper())
        output.seek(0)
        
        # Devolver la imagen como una respuesta de streaming con el tipo de contenido adecuado
        return StreamingResponse(output, media_type=f"image/{format}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/")
async def download_file(file_path: str):
    normalized_file_path = file_path.replace("/", os.path.sep)
    if not os.path.isfile(normalized_file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(normalized_file_path, media_type='application/octet-stream', filename=os.path.basename(normalized_file_path))

@app.post("/compress-image/")
async def compress_image(file: UploadFile = File(...), quality: int = Form(20)):
    try:
        if file.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(status_code=400, detail="Invalid file type. Only jpg and png are allowed.")

        # Leer el archivo cargado
        image = Image.open(file.file)

        # Convertir la imagen de RGBA a RGB si es necesario
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        
        # Crear un buffer para almacenar la imagen comprimida
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=quality)
        buffer.seek(0)

        # Generar un nombre de archivo para la imagen comprimida
        compressed_filename = f"compressed_{file.filename}"
        compressed_file_path = os.path.join(UPLOAD_DIR, compressed_filename)
        
        # Guardar la imagen comprimida en el directorio de subida
        with open(compressed_file_path, "wb") as f:
            f.write(buffer.getbuffer())

        normalized_compressed_file_path = compressed_file_path.replace("\\", "/")
        return {"compressed_file_path": normalized_compressed_file_path}
    
    except UnidentifiedImageError:
        logging.error(f"Cannot identify image file {file.filename}")
        return JSONResponse(status_code=400, content={"error": "Cannot identify image file."})
    
    except Exception as e:
        logging.error(f"Error compressing image: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
