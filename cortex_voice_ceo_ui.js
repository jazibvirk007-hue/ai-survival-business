/* V12 Voice CEO browser adapter. Uses browser speech recognition when available. */
(() => {
  "use strict";
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recognition = null;
  let listening = false;

  const setState = (text) => {
    const node = document.querySelector("[data-voice-state]");
    if (node) node.textContent = text;
  };

  const setReply = (text) => {
    const node = document.querySelector("[data-voice-reply]");
    if (node) node.textContent = text;
  };

  const speak = (text) => {
    if (!window.speechSynthesis || !text) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text.slice(0, 2000));
    utterance.rate = 1;
    window.speechSynthesis.speak(utterance);
  };

  const sendTranscript = async (transcript) => {
    setState("PROCESSING");
    try {
      const response = await fetch("/api/voice/command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "voice request failed");
      setReply(data.response || "Cortex completed the request.");
      speak(data.response || "Cortex completed the request.");
      setState("READY");
    } catch (error) {
      setReply("CORTEX VOICE ERROR: " + error.message);
      setState("ERROR");
    }
  };

  const stop = () => {
    if (recognition) recognition.stop();
    listening = false;
    setState("READY");
  };

  const start = () => {
    if (!Recognition) {
      setState("UNSUPPORTED");
      setReply("Browser speech recognition is unavailable. Configure a Cortex speech-to-text adapter instead.");
      return;
    }
    if (listening) return;
    recognition = new Recognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onstart = () => { listening = true; setState("LISTENING"); };
    recognition.onerror = (event) => { listening = false; setState("ERROR"); setReply("Microphone error: " + event.error); };
    recognition.onend = () => { listening = false; if (document.visibilityState !== "hidden") setState("READY"); };
    recognition.onresult = (event) => {
      const transcript = event.results?.[0]?.[0]?.transcript || "";
      if (transcript.trim()) sendTranscript(transcript);
    };
    recognition.start();
  };

  window.CortexVoiceCEO = { start, stop, sendTranscript };

  document.addEventListener("DOMContentLoaded", () => {
    const startButton = document.querySelector("[data-voice-start]");
    const stopButton = document.querySelector("[data-voice-stop]");
    if (startButton) startButton.addEventListener("click", start);
    if (stopButton) stopButton.addEventListener("click", stop);
    if (!Recognition) setState("ADAPTER REQUIRED");
    else setState("READY");
  });
})();
