from fastapi import FastAPI, File, UploadFile
from io import BytesIO
from PIL import Image
import tensorflow as tf
import numpy as np
from mangum import Mangum

app = FastAPI()

MODEL = None
CLASS_NAMES = ["Ishan", "Vinuwara", "Ridmika"]

def load_model():
    global MODEL
    if MODEL is None:
        MODEL = tf.keras.models.load_model("models")

def read_file_as_image(data) -> np.ndarray:
    image = Image.open(BytesIO(data))
    # Resize the image to 256x256
    image = image.resize((256, 256))
    image = np.array(image)
    return image

@app.post("/")
async def predict(
    file: UploadFile = File(...)
):
    load_model()  # Ensure model is loaded before prediction
    image = read_file_as_image(await file.read())
    img_batch = np.expand_dims(image, 0)

    predictions = MODEL.predict(img_batch)

    predicted_class = CLASS_NAMES[np.argmax(predictions[0])]
    confidence = np.max(predictions[0])*100
    print(confidence)
    if confidence < 50:
        return {'result': 'Not'}
    else:
        return {'result': 'Yes'}

handler = Mangum(app, lifespan="auto")