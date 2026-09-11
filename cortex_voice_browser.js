(() => {
  "use strict";
  const MAX_TRANSCRIPT = 4000;
  const state = { listening: false, recognition: null };

  function supported() {
    return Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);
  }

  function startVoiceCEO({ onTranscript, onResult, onError } = {}) {
    if (!supported()) throw new Error("Browser speech recognition is not available");
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new Recognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.continuous = false;
    recognition.maxAlternatives = 1;
    recognition.onstart = () => { state.listening = true; };
    recognition.onend = () => { state.listening = false; };
    recognition.onerror = (event) => { state.listening = false; if (onError) onError(event.error || "speech_error"); };
    recognition.onresult = async (event) => {
      const transcript = String(event.results?.[0]?.[0]?.transcript || "").trim().slice(0, MAX_TRANSCRIPT);
      if (!transcript) return;
      if (onTranscript) onTranscript(transcript);
      try {
        const response = await fetch("/api/voice", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ transcript })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "voice_request_failed");
        if (onResult) onResult(data);
      } catch (error) {
        if (onError) onError(error.message || "voice_request_failed");
      }
    };
    state.recognition = recognition;
    recognition.start();
    return recognition;
  }

  function stopVoiceCEO() {
    if (state.recognition) state.recognition.stop();
    state.listening = false;
  }

  window.CortexVoiceCEO = { supported, start: startVoiceCEO, stop: stopVoiceCEO, state };
})();
