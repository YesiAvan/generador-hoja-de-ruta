from flask import Flask, request, jsonify
from PIL import Image, UnidentifiedImageError
import pytesseract, zipfile, io

app = Flask(__name__)

@app.route("/ruta", methods=["POST"])
def generar_ruta():
    file = request.files.get("attachment")
    if not file:
        return jsonify({"error": "No se recibió archivo Excel"}), 400

    try:
        zip_file = zipfile.ZipFile(file)
        image_files = [f for f in zip_file.namelist() if f.startswith("xl/media/") and f.lower().endswith(('.png', '.jpg', '.jpeg'))]

        if not image_files:
            return jsonify({"error": "No se encontró ninguna imagen en el archivo Excel"}), 400

        img_data = zip_file.read(image_files[0])
        img = Image.open(io.BytesIO(img_data))

        texto = pytesseract.image_to_string(img)
        direcciones = [line.strip() for line in texto.split("\n") if len(line.strip()) > 5]
        direcciones = [d for d in direcciones if not d.lower().startswith("tiempo")]

        if not direcciones:
            return jsonify({"error": "No se pudieron detectar direcciones en la imagen"}), 400

        direcciones_maps = "/".join([d.replace(" ", "+") for d in direcciones])
        maps_url = f"https://www.google.com/maps/dir/{direcciones_maps}"

        mensaje = "📦 ¡Hola! Te comparto la hoja de ruta:\n\n"
        for i, dir in enumerate(direcciones, 1):
            mensaje += f"{i}️⃣ {dir}\n"
        mensaje += f"\n🗺️ Ruta: {maps_url}\n\n¡Buen viaje! 🚛📲"

        return jsonify({"mensaje": mensaje, "link": maps_url})

    except zipfile.BadZipFile:
        return jsonify({"error": "El archivo no es un Excel válido"}), 400
    except UnidentifiedImageError:
        return jsonify({"error": "La imagen no pudo ser leída"}), 400
    except Exception as e:
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500
