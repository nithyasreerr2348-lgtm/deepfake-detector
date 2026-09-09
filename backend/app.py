from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import pipeline
from PIL import Image
import cv2
import os
import tempfile
import numpy as np


app = Flask(__name__)
CORS(app)

# Maximum upload size: 100 MB
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024


# ==========================================
# LOAD AI MODEL
# ==========================================

print("Loading Deepfake Detection AI model...")

classifier = pipeline(
    "image-classification",
    model="dima806/deepfake_vs_real_image_detection",
    device=-1
)

print("AI model loaded successfully!")


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():

    return jsonify({
        "message": "DeepGuard AI backend is running"
    })


# ==========================================
# ANALYZE VIDEO
# ==========================================

@app.route("/analyze", methods=["POST"])
def analyze_video():

    if "video" not in request.files:

        return jsonify({
            "error": "No video uploaded"
        }), 400


    video = request.files["video"]

    if video.filename == "":

        return jsonify({
            "error": "No video selected"
        }), 400


    # Get original file extension
    extension = os.path.splitext(video.filename)[1]

    if not extension:
        extension = ".mp4"


    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=extension
    )

    temp_path = temp_file.name

    temp_file.close()


    try:

        # Save uploaded video
        video.save(temp_path)


        # Open video
        capture = cv2.VideoCapture(temp_path)


        if not capture.isOpened():

            return jsonify({
                "error": "Unable to open video"
            }), 400


        # Get total number of frames
        total_frames = int(
            capture.get(cv2.CAP_PROP_FRAME_COUNT)
        )


        if total_frames <= 0:

            capture.release()

            return jsonify({
                "error": "No frames found in video"
            }), 400


        # ==========================================
        # SELECT FRAMES
        # ==========================================

        MAX_FRAMES = 12

        frame_count = min(
            total_frames,
            MAX_FRAMES
        )


        frame_indices = np.linspace(
            0,
            total_frames - 1,
            frame_count,
            dtype=int
        )


        fake_scores = []

        frames_analyzed = 0


        # ==========================================
        # AI ANALYSIS
        # ==========================================

        for frame_index in frame_indices:

            capture.set(
                cv2.CAP_PROP_POS_FRAMES,
                int(frame_index)
            )


            success, frame = capture.read()


            if not success:
                continue


            # OpenCV uses BGR
            # Convert BGR -> RGB

            rgb_frame = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )


            # Convert frame to PIL image
            image = Image.fromarray(rgb_frame)


            # Run AI model
            predictions = classifier(
                image,
                top_k=2
            )


            fake_probability = None


            # Find Fake / Real prediction
            for prediction in predictions:

                label = prediction["label"].lower()
                score = prediction["score"]


                if "fake" in label:

                    fake_probability = score
                    break


                elif "real" in label:

                    fake_probability = 1 - score
                    break


            # If model labels are unexpected,
            # use the highest prediction score
            if fake_probability is None:

                fake_probability = predictions[0]["score"]


            fake_scores.append(
                fake_probability
            )


            frames_analyzed += 1


        capture.release()


        # ==========================================
        # CALCULATE FINAL RESULT
        # ==========================================

        if not fake_scores:

            return jsonify({
                "error": "Unable to analyze video frames"
            }), 400


        average_fake_score = (
            sum(fake_scores) /
            len(fake_scores)
        )


        # Determine result
        if average_fake_score >= 0.5:

            result = "Likely Deepfake"

            confidence = round(
                average_fake_score * 100
            )

        else:

            result = "Likely Real"

            confidence = round(
                (1 - average_fake_score) * 100
            )


        return jsonify({

            "result": result,

            "confidence": confidence,

            "frames_analyzed": frames_analyzed,

            "message":
                "AI analysis completed successfully"

        })


    except Exception as error:

        print("ERROR:", error)

        return jsonify({

            "error":
                "AI analysis failed: " + str(error)

        }), 500


    finally:

        # Delete temporary video
        if os.path.exists(temp_path):

            os.remove(temp_path)


# ==========================================
# START SERVER
# ==========================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=7860,
        debug=False
    )