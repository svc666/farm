from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# Initialize Firebase
cred = credentials.Certificate("path/to/serviceAccountKey.json")  # Replace with your Firebase key
firebase_admin.initialize_app(cred)
db = firestore.client()

# Crop growth times (seconds)
CROP_GROWTH_TIME = {
    "Wheat": 5,
    "Corn": 10,
    "Carrot": 15
}

# 🌱 Plant a crop
@app.route("/plant", methods=["POST"])
def plant_crop():
    data = request.json
    user_id = data["user_id"]
    tile_index = data["tile_index"]
    crop_name = data["crop_name"]

    # Get user's land data
    user_ref = db.collection("users").document(user_id)
    user_data = user_ref.get().to_dict()

    if not user_data or crop_name not in user_data["crops"] or user_data["crops"][crop_name] <= 0:
        return jsonify({"error": "Not enough crops available!"}), 400

    # Reduce crop count and update land tile
    user_data["crops"][crop_name] -= 1
    user_data["land_tiles"][str(tile_index)] = {"crop": crop_name, "status": "growing"}

    user_ref.set(user_data)
    return jsonify({"message": f"{crop_name} planted successfully!", "land": user_data["land_tiles"]})

# 🌾 Harvest a crop
@app.route("/harvest", methods=["POST"])
def harvest_crop():
    data = request.json
    user_id = data["user_id"]
    tile_index = data["tile_index"]

    user_ref = db.collection("users").document(user_id)
    user_data = user_ref.get().to_dict()

    if not user_data or str(tile_index) not in user_data["land_tiles"]:
        return jsonify({"error": "Invalid land tile!"}), 400

    crop_name = user_data["land_tiles"][str(tile_index)]["crop"]
    if not crop_name:
        return jsonify({"error": "No crop to harvest!"}), 400

    # Harvest and update storage
    user_data["storage"][crop_name] = user_data["storage"].get(crop_name, 0) + 2
    user_data["land_tiles"][str(tile_index)] = {"crop": None}

    user_ref.set(user_data)
    return jsonify({"message": f"{crop_name} harvested!", "storage": user_data["storage"]})

# 📦 Get storage room data
@app.route("/storage/<user_id>", methods=["GET"])
def get_storage(user_id):
    user_ref = db.collection("users").document(user_id)
    user_data = user_ref.get().to_dict()

    if not user_data:
        return jsonify({"error": "User not found!"}), 404

    return jsonify({"storage": user_data["storage"]})

if __name__ == "__main__":
    app.run(debug=True)
