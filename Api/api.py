from flask import Flask, request, jsonify
import numpy as np
from io import BytesIO
from PIL import Image
import tensorflow as tf

app = Flask(__name__)

MODEL = tf.keras.models.load_model("Model")

CLASS_NAMES = ["Ishan", "Ridmika", "Vinuwawra"]

@app.route("/ping")
def ping():
    return "Hello, I am alive"

def read_file_as_image(data, target_size=(256, 256)) -> np.ndarray:
    image = Image.open(BytesIO(data))
    # Resize the image
    image = image.resize(target_size)
    image = np.array(image)
    return image


@app.route("/prediction", methods=["POST"])
def predict():
    file = request.files["file"]
    image = read_file_as_image(file.read())
    img_batch = np.expand_dims(image, 0)

    predictions = MODEL.predict(img_batch)

    predicted_class = CLASS_NAMES[np.argmax(predictions[0])]
    confidence = np.max(predictions[0])
    if confidence < 50:
        response = {"prediction": "Not"}
    else:
        response = {"prediction": "Yes"}

    return jsonify(response)

if __name__ == "__main__":
    app.run(port=8000)
