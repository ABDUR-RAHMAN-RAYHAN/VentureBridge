(function () {
  var stream = null;
  var video, canvas, ctx;
  var captured = { 1: null, 2: null, 3: null };

  async function startCamera() {
    var statusEl = document.getElementById("camStatus");
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
      video = document.getElementById("camVideo");
      video.srcObject = stream;
      await video.play();
      document.getElementById("camStartBtn").style.display = "none";
      document.getElementById("camLiveArea").style.display = "block";
      if (statusEl) statusEl.textContent = "Camera live. Capture 3 photos (e.g. front, left turn, right turn).";
    } catch (err) {
      if (statusEl) statusEl.textContent = "Could not access camera: " + err.message +
        ". Please allow camera permission — live capture is required for verification.";
    }
  }

  function capturePhoto(slot) {
    if (!video) return;
    canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    var dataUrl = canvas.toDataURL("image/jpeg", 0.85);
    captured[slot] = dataUrl;

    var img = document.getElementById("preview" + slot);
    img.src = dataUrl;
    img.style.display = "block";
    document.getElementById("placeholder" + slot).style.display = "none";
    document.getElementById("photo_" + slot).value = dataUrl;

    checkAllCaptured();
  }

  function retake(slot) {
    captured[slot] = null;
    document.getElementById("photo_" + slot).value = "";
    document.getElementById("preview" + slot).style.display = "none";
    document.getElementById("placeholder" + slot).style.display = "flex";
    checkAllCaptured();
  }

  function checkAllCaptured() {
    var allDone = captured[1] && captured[2] && captured[3];
    var submitBtn = document.getElementById("verifySubmitBtn");
    if (submitBtn) submitBtn.disabled = !allDone;
  }

  window.vbWebcam = { startCamera: startCamera, capturePhoto: capturePhoto, retake: retake };
})();
