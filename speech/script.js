let chunks = [];
let mediaRecorder = null;
let mediaStream = null;
let isRecording = false;

async function ensureStream() {
  if (mediaStream) return mediaStream;
  mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  return mediaStream;
}

function getSupportedMimeType() {
  const candidates = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/ogg;codecs=opus',
    'audio/ogg'
  ];
  for (const type of candidates) {
    if (MediaRecorder.isTypeSupported(type)) return type;
  }
  return '';
}

function startRecording() {
  if (isRecording) return;
  chunks = [];
  const mimeType = getSupportedMimeType();
  mediaRecorder = new MediaRecorder(mediaStream, mimeType ? { mimeType } : undefined);
  mediaRecorder.ondataavailable = e => {
    if (e.data && e.data.size > 0) chunks.push(e.data);
  };
  mediaRecorder.onstop = () => {
    if (!chunks.length) return;
    const type = mediaRecorder.mimeType || 'audio/webm';
    const blob = new Blob(chunks, { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const ts = new Date().toISOString().replace(/[:.]/g, '-');
    const ext = type.includes('ogg') ? 'ogg' : 'webm';
    a.href = url;
    a.download = `recording-input-${ts}.${ext}`;
    a.innerText = `Download ${a.download}`;
    document.getElementById('downloads').appendChild(a);
    const click = document.createEvent('MouseEvents');
    click.initEvent('click', true, true);
    a.dispatchEvent(click);
  };
  mediaRecorder.start();
  isRecording = true;
  setStatus('Recording...');
}

function stopRecording() {
  if (!isRecording) return;
  try {
    mediaRecorder.stop();
  } catch {}
  isRecording = false;
  setStatus('Idle');
}

function setStatus(text) {
  const el = document.getElementById('status');
  if (el) el.textContent = text;
}

function setupPressAndHold(btn) {
  const start = async e => {
    e.preventDefault();
    btn.classList.add('recording');
    try {
      await ensureStream();
      startRecording();
      window.addEventListener('pointerup', onPointerUpOnce, { once: true });
      window.addEventListener('pointercancel', onPointerUpOnce, { once: true });
      window.addEventListener('blur', onPointerUpOnce, { once: true });
    } catch (err) {
      btn.classList.remove('recording');
      setStatus('Microphone access denied');
      console.error('Error accessing microphone:', err);
    }
  };
  const end = () => {
    btn.classList.remove('recording');
    stopRecording();
  };
  const onPointerUpOnce = () => end();
  btn.addEventListener('pointerdown', start);
}

window.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('recordBtn');
  setupPressAndHold(btn);
});


