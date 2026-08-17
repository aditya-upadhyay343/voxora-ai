/**
 * script.js
 * ----------
 * Frontend logic for the AI Speech-to-Text Converter.
 *
 * This file is loaded on BOTH the home page (index.html) and the
 * history page (history.html). Each section below checks whether the
 * relevant elements exist on the current page before running, so it
 * is safe to include on both pages.
 */

// =====================================================================
// SECTION 1: Microphone recording + file upload + transcription
// (runs on index.html)
// =====================================================================

(function initHomePage() {
  const startRecordBtn = document.getElementById("startRecordBtn");
  const stopRecordBtn = document.getElementById("stopRecordBtn");
  const recordingStatus = document.getElementById("recordingStatus");
  const recordingTimer = document.getElementById("recordingTimer");
  const audioPreview = document.getElementById("audioPreview");
  const audioFileInput = document.getElementById("audioFileInput");
  const languageSelect = document.getElementById("languageSelect");
  const transcribeBtn = document.getElementById("transcribeBtn");
  const loadingIndicator = document.getElementById("loadingIndicator");
  const errorBox = document.getElementById("errorBox");

  const resultText = document.getElementById("resultText");
  const resultLanguage = document.getElementById("resultLanguage");
  const resultWordCount = document.getElementById("resultWordCount");
  const resultCharCount = document.getElementById("resultCharCount");
  const resultStatus = document.getElementById("resultStatus");

  const copyBtn = document.getElementById("copyBtn");
  const downloadBtn = document.getElementById("downloadBtn");
  const clearBtn = document.getElementById("clearBtn");

  // If these elements don't exist, we are not on the home page - stop here.
  if (!startRecordBtn) {
    return;
  }

  let mediaRecorder = null;
  let recordedChunks = [];
  let recordedBlob = null;
  let selectedFile = null; // File chosen via the upload input
  let timerInterval = null;
  let secondsElapsed = 0;
  let currentTranscriptionId = null;

  // ---------------------- Recording timer helpers ----------------------

  function formatTime(totalSeconds) {
    const minutes = Math.floor(totalSeconds / 60).toString().padStart(2, "0");
    const seconds = (totalSeconds % 60).toString().padStart(2, "0");
    return `${minutes}:${seconds}`;
  }

  function startTimer() {
    secondsElapsed = 0;
    recordingTimer.textContent = formatTime(0);
    timerInterval = setInterval(() => {
      secondsElapsed += 1;
      recordingTimer.textContent = formatTime(secondsElapsed);
    }, 1000);
  }

  function stopTimer() {
    clearInterval(timerInterval);
  }

  // ---------------------- Microphone recording ----------------------

  startRecordBtn.addEventListener("click", async () => {
    hideError();

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      showError("Your browser does not support microphone recording.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      recordedChunks = [];
      mediaRecorder = new MediaRecorder(stream);

      mediaRecorder.addEventListener("dataavailable", (event) => {
        if (event.data.size > 0) {
          recordedChunks.push(event.data);
        }
      });

      mediaRecorder.addEventListener("stop", () => {
        recordedBlob = new Blob(recordedChunks, { type: "audio/webm" });
        selectedFile = null; // recording takes priority over any uploaded file
        audioFileInput.value = "";

        const audioUrl = URL.createObjectURL(recordedBlob);
        audioPreview.src = audioUrl;
        audioPreview.classList.remove("hidden");

        // Stop all microphone tracks so the browser's "recording" indicator turns off.
        stream.getTracks().forEach((track) => track.stop());
      });

      mediaRecorder.start();
      startTimer();

      recordingStatus.textContent = "Recording...";
      recordingStatus.classList.remove("status-idle");
      recordingStatus.classList.add("status-recording");

      startRecordBtn.disabled = true;
      stopRecordBtn.disabled = false;
    } catch (err) {
      showError(
        "Could not access the microphone. Please allow microphone " +
        "permissions in your browser and try again."
      );
    }
  });

  stopRecordBtn.addEventListener("click", () => {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
    }
    stopTimer();

    recordingStatus.textContent = "Recorded";
    recordingStatus.classList.remove("status-recording");
    recordingStatus.classList.add("status-idle");

    startRecordBtn.disabled = false;
    stopRecordBtn.disabled = true;
  });

  // ---------------------- File upload ----------------------

  audioFileInput.addEventListener("change", () => {
    if (audioFileInput.files.length > 0) {
      selectedFile = audioFileInput.files[0];
      recordedBlob = null; // uploading a file takes priority over any recording

      const audioUrl = URL.createObjectURL(selectedFile);
      audioPreview.src = audioUrl;
      audioPreview.classList.remove("hidden");
      hideError();
    }
  });

  // ---------------------- Transcribe ----------------------

  transcribeBtn.addEventListener("click", async () => {
    hideError();

    const audioToSend = selectedFile || recordedBlob;
    if (!audioToSend) {
      showError("Please record audio or upload an audio file first.");
      return;
    }

    const formData = new FormData();
    // Give recorded blobs a sensible filename with the correct extension.
    if (selectedFile) {
      formData.append("audio", selectedFile, selectedFile.name);
    } else {
      formData.append("audio", audioToSend, "recording.webm");
    }
    formData.append("language", languageSelect.value);

    setLoading(true);

    try {
      const response = await fetch("/api/transcribe", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        showError(data.error || "Something went wrong while transcribing.");
        setResultStatus("Failed");
        return;
      }

      const record = data.transcription;
      currentTranscriptionId = record.id;

      resultText.value = record.transcription;
      resultLanguage.textContent = `Language: ${record.detected_language || record.language}`;
      resultWordCount.textContent = `Words: ${record.word_count}`;
      resultCharCount.textContent = `Characters: ${record.character_count}`;
      setResultStatus("Success");

      downloadBtn.disabled = false;
    } catch (err) {
      showError("Could not reach the server. Is the Flask app running?");
      setResultStatus("Failed");
    } finally {
      setLoading(false);
    }
  });

  // ---------------------- Result actions ----------------------

  copyBtn.addEventListener("click", async () => {
    if (!resultText.value) {
      return;
    }
    try {
      await navigator.clipboard.writeText(resultText.value);
      const original = copyBtn.textContent;
      copyBtn.textContent = "✅ Copied!";
      setTimeout(() => (copyBtn.textContent = original), 1500);
    } catch (err) {
      // Fallback for browsers without Clipboard API support.
      resultText.select();
      document.execCommand("copy");
    }
  });

  downloadBtn.addEventListener("click", () => {
    if (currentTranscriptionId === null) {
      return;
    }
    window.location.href = `/api/download/${currentTranscriptionId}`;
  });

  clearBtn.addEventListener("click", () => {
    resultText.value = "";
    resultLanguage.textContent = "Language: -";
    resultWordCount.textContent = "Words: 0";
    resultCharCount.textContent = "Characters: 0";
    setResultStatus("waiting");
    downloadBtn.disabled = true;
    currentTranscriptionId = null;

    selectedFile = null;
    recordedBlob = null;
    audioFileInput.value = "";
    audioPreview.classList.add("hidden");
    audioPreview.removeAttribute("src");
    hideError();
  });

  // ---------------------- Small UI helpers ----------------------

  function setLoading(isLoading) {
    loadingIndicator.classList.toggle("hidden", !isLoading);
    transcribeBtn.disabled = isLoading;
  }

  function setResultStatus(status) {
    resultStatus.textContent = `Status: ${status}`;
  }

  function showError(message) {
    errorBox.textContent = message;
    errorBox.classList.remove("hidden");
  }

  function hideError() {
    errorBox.textContent = "";
    errorBox.classList.add("hidden");
  }
})();

// =====================================================================
// SECTION 2: Transcription history page
// (runs on history.html)
// =====================================================================

(function initHistoryPage() {
  const historyTable = document.getElementById("historyTable");
  const historyTableBody = document.getElementById("historyTableBody");
  const emptyState = document.getElementById("emptyState");

  // If these elements don't exist, we are not on the history page - stop here.
  if (!historyTable) {
    return;
  }

  async function loadHistory() {
    try {
      const response = await fetch("/api/history");
      const data = await response.json();
      renderHistory(data.history || []);
    } catch (err) {
      emptyState.textContent = "Could not load history. Is the Flask app running?";
      emptyState.classList.remove("hidden");
    }
  }

  function renderHistory(records) {
    historyTableBody.innerHTML = "";

    if (records.length === 0) {
      emptyState.classList.remove("hidden");
      historyTable.classList.add("hidden");
      return;
    }

    emptyState.classList.add("hidden");
    historyTable.classList.remove("hidden");

    records.forEach((record) => {
      const row = document.createElement("tr");

      const dateCell = document.createElement("td");
      dateCell.textContent = record.created_at;

      const langCell = document.createElement("td");
      langCell.textContent = record.detected_language || record.language;

      const textCell = document.createElement("td");
      textCell.classList.add("history-text-cell");
      textCell.textContent = record.transcription;

      const actionsCell = document.createElement("td");
      actionsCell.classList.add("row-actions");

      const downloadLink = document.createElement("a");
      downloadLink.href = `/api/download/${record.id}`;
      downloadLink.className = "btn btn-secondary";
      downloadLink.textContent = "⬇️ TXT";
      actionsCell.appendChild(downloadLink);

      const deleteBtn = document.createElement("button");
      deleteBtn.className = "btn btn-outline";
      deleteBtn.textContent = "🗑️ Delete";
      deleteBtn.addEventListener("click", () => deleteRecord(record.id));
      actionsCell.appendChild(deleteBtn);

      row.appendChild(dateCell);
      row.appendChild(langCell);
      row.appendChild(textCell);
      row.appendChild(actionsCell);

      historyTableBody.appendChild(row);
    });
  }

  async function deleteRecord(id) {
    const confirmed = window.confirm("Delete this transcription permanently?");
    if (!confirmed) {
      return;
    }
    try {
      const response = await fetch(`/api/history/${id}`, { method: "DELETE" });
      if (response.ok) {
        loadHistory();
      }
    } catch (err) {
      window.alert("Could not delete this record. Is the Flask app running?");
    }
  }

  loadHistory();
})();
