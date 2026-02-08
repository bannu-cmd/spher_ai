// Initialize Speech Recognition
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = new SpeechRecognition();
recognition.lang = 'en-US';
recognition.interimResults = false;

const sphere = document.getElementById('sphere');
const statusText = document.getElementById('status');
const transcriptText = document.getElementById('transcript');
const aiText = document.getElementById('ai-response');

// 1. Start listening when the sphere is clicked
sphere.onclick = () => {
    recognition.start();
    sphere.classList.add('listening');
    statusText.innerText = "Listening...";
};

// 2. Process the speech result
recognition.onresult = (event) => {
    const userSpeech = event.results[0][0].transcript;
    transcriptText.innerText = "You: " + userSpeech;
    sphere.classList.remove('listening');
    statusText.innerText = "Grok is thinking...";

    // Send the text to our Flask backend
    sendToGrok(userSpeech);
};
sphere.classList.add('thinking');
// 3. Communicate with Flask & Grok
async function sendToGrok(text) {
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });

        const data = await response.json();
        
        // Update UI with Grok's short response
        aiText.innerText = "Grok: " + data.text;
        statusText.innerText = "Grok is speaking...";

        // 4. Play the Text-to-Speech audio
        const audio = new Audio(data.audio_url + '?cb=' + new Date().getTime());
        audio.play();

        audio.onended = () => {
            statusText.innerText = "Tap to talk again";
        };

    } catch (error) {
        console.error("Error:", error);
        statusText.innerText = "Error connecting to server.";
    }
}
sphere.classList.remove('thinking');
recognition.onerror = () => {
    sphere.classList.remove('listening');
    statusText.innerText = "Try again?";
};