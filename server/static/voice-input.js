(() => {
  let button = null;
  let textarea = null;
  let onStatus = null;
  let mediaRecorder = null;
  let chunks = [];
  let stream = null;
  let recording = false;
  let visible = false;

  function pickMimeType() {
    const candidates = [
      "audio/webm;codecs=opus",
      "audio/webm",
      "audio/ogg;codecs=opus",
      "audio/mp4",
    ];
    for (const type of candidates) {
      if (window.MediaRecorder && MediaRecorder.isTypeSupported(type)) {
        return type;
      }
    }
    return "";
  }

  function setStatus(text) {
    if (onStatus) onStatus(text);
  }

  function setButtonLabel(text) {
    if (button) button.textContent = text;
  }

  async function stopTracks() {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }
  }

  async function transcribeBlob(blob) {
    const ext = blob.type.includes("ogg") ? "ogg" : blob.type.includes("mp4") ? "mp4" : "webm";
    const form = new FormData();
    form.append("audio", blob, `recording.${ext}`);
    const res = await fetch("/api/asr/transcribe", { method: "POST", body: form });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.detail || res.statusText || "ASR error");
    }
    return (data.text || "").trim();
  }

  async function startRecording() {
    if (!visible || !textarea || recording) return;
    chunks = [];
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mimeType = pickMimeType();
    mediaRecorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
    mediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) chunks.push(event.data);
    };
    mediaRecorder.onstop = async () => {
      recording = false;
      setButtonLabel("🎤 Голосом");
      await stopTracks();
      const blob = new Blob(chunks, { type: mediaRecorder.mimeType || "audio/webm" });
      chunks = [];
      if (!blob.size) {
        setStatus("Запись пуста");
        return;
      }
      if (button) button.disabled = true;
      setStatus("Распознаём речь…");
      try {
        const text = await transcribeBlob(blob);
        if (!text) {
          setStatus("Речь не распознана");
          return;
        }
        textarea.value = text;
        textarea.focus();
        setStatus("Текст распознан. Проверьте ответ и отправьте.");
      } catch (err) {
        setStatus(`❌ ${err.message}`);
      } finally {
        if (button && visible) button.disabled = false;
      }
    };
    mediaRecorder.start();
    recording = true;
    setButtonLabel("⏹ Стоп");
    setStatus("Запись… нажмите ещё раз, чтобы остановить");
  }

  async function stopRecording() {
    if (!mediaRecorder || mediaRecorder.state === "inactive") return;
    mediaRecorder.stop();
  }

  async function toggleRecording() {
    if (!visible) return;
    if (recording) {
      await stopRecording();
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      setStatus("Браузер не поддерживает запись с микрофона");
      return;
    }
    try {
      await startRecording();
    } catch (err) {
      await stopTracks();
      recording = false;
      setButtonLabel("🎤 Голосом");
      setStatus(`❌ ${err.message}`);
    }
  }

  window.VoiceInput = {
    bind(btn, textArea, statusCallback) {
      button = btn;
      textarea = textArea;
      onStatus = statusCallback;
      button.onclick = () => toggleRecording();
    },

    setVisible(show) {
      visible = show;
      if (button) {
        button.classList.toggle("hidden", !show);
        button.disabled = false;
      }
      if (!show && recording) {
        stopRecording();
      }
      if (!show) {
        setButtonLabel("🎤 Голосом");
      }
    },
  };
})();
