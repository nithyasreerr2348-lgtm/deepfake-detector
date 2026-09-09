const videoInput = document.getElementById("videoInput");

const videoPreview =
    document.getElementById("videoPreview");

const videoContainer =
    document.getElementById("videoContainer");

const fileName =
    document.getElementById("fileName");

const analyzeButton =
    document.getElementById("analyzeButton");

const resultBox =
    document.getElementById("resultBox");

const resultText =
    document.getElementById("resultText");

const confidenceValue =
    document.getElementById("confidenceValue");


// ===============================
// VIDEO SELECTION
// ===============================

videoInput.addEventListener("change", function () {

    const file = this.files[0];

    if (!file) {
        return;
    }

    fileName.textContent =
        "Selected: " + file.name;

    const videoURL =
        URL.createObjectURL(file);

    videoPreview.src = videoURL;

    videoContainer.style.display = "block";

    resultBox.style.display = "none";
});


// ===============================
// ANALYZE VIDEO
// ===============================

analyzeButton.addEventListener("click", async function () {

    const file = videoInput.files[0];

    if (!file) {

        alert("Please select a video first.");

        return;
    }


    // Show analyzing message

    resultBox.style.display = "block";

    resultText.textContent =
        "Analyzing video...";

    confidenceValue.textContent =
        "--";


    // Create form data

    const formData = new FormData();

    formData.append("video", file);


    try {

        // Send video to Flask backend

        const response = await fetch(
            "http://127.0.0.1:5000/analyze",
            {
                method: "POST",
                body: formData
            }
        );


        const data = await response.json();


        // Display backend result

        if (response.ok) {

            resultText.textContent =
                data.result;

            confidenceValue.textContent =
                data.confidence + "%";

            console.log(
                "Frames analyzed:",
                data.frames_analyzed
            );

        } else {

            resultText.textContent =
                "Analysis failed";

            confidenceValue.textContent =
                "--";

            console.error(data.error);
        }


    } catch (error) {

        console.error(error);

        resultText.textContent =
            "Unable to connect to AI backend";

        confidenceValue.textContent =
            "--";
    }

});