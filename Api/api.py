from flask import Flask, request, jsonify
import numpy as np
from io import BytesIO
from PIL import Image
import tensorflow as tf

app = Flask(__name__)

MODEL_FILE = "model.tflite"

CLASS_NAMES = ["Ishan", "Ridmika", "Vinuwawra"]

def read_file_as_image(data, target_size=(256, 256)) -> np.ndarray:
    image = Image.open(BytesIO(data))
    # Resize the image
    image = image.resize(target_size)
    image = np.array(image)
    return image

def load_model(model_file):
    interpreter = tf.lite.Interpreter(model_path=model_file)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    return interpreter, input_details, output_details

def predict_with_tflite(interpreter, input_details, output_details, image):
    input_shape = input_details[0]['shape']
    input_data = np.expand_dims(image, axis=0).astype(np.float32)
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])
    return output_data

interpreter, input_details, output_details = load_model(MODEL_FILE)

@app.route("/ping")
def ping():
    return "Hello, I am alive"

@app.route("/prediction", methods=["POST"])
def predict():
    file = request.files["file"]
    image = read_file_as_image(file.read())

    predictions = predict_with_tflite(interpreter, input_details, output_details, image)

    confidence = np.max(predictions[0])
    print(confidence)
    if confidence < 0.5:
        response = {"result": "Not"}
    else:
        response = {"result": "Yes"}

    return jsonify(response)

if __name__ == "__main__":
    app.run(port=8000)
