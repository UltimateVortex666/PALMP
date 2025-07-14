// AI Palm Detection using MediaPipe Hands
class PalmDetector {
    constructor() {
        this.hands = null;
        this.camera = null;
        this.video = document.getElementById('camera-preview');
        this.canvas = document.getElementById('palm-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.isDetecting = false;
        this.palmDetected = false;
        this.capturedImage = null;
        this.isPaymentScan = !!document.getElementById('palm-upload-form');
        this.setupEventListeners();
        this.initializeHands();
    }

    async initializeHands() {
        this.hands = new Hands({
            locateFile: (file) => {
                return `https://cdn.jsdelivr.net/npm/@mediapipe/hands@0.4.1646424915/${file}`;
            }
        });
        this.hands.setOptions({
            maxNumHands: 1,
            modelComplexity: 1,
            minDetectionConfidence: 0.5,
            minTrackingConfidence: 0.5
        });
        this.hands.onResults((results) => this.onHandResults(results));
    }

    setupEventListeners() {
        const startBtn = document.getElementById('start-camera-btn');
        const captureBtn = document.getElementById('capture-palm-btn');
        const retakeBtn = document.getElementById('retake-palm-btn');
        if (startBtn) startBtn.addEventListener('click', () => this.startCamera());
        if (captureBtn) captureBtn.addEventListener('click', () => this.capturePalm());
        if (retakeBtn) retakeBtn.addEventListener('click', () => this.retakePalm());
    }

    async startCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'environment'
                }
            });
            this.video.srcObject = stream;
            this.video.addEventListener('loadedmetadata', () => {
                this.canvas.width = this.video.videoWidth;
                this.canvas.height = this.video.videoHeight;
                this.startDetection();
                this.updateStatus('Camera started. Position your palm in the frame.');
                this.showCaptureButton();
            }, { once: true });
        } catch (error) {
            console.error('Error accessing camera:', error);
            this.updateStatus('Error: Could not access camera. Please check permissions.');
        }
    }

    startDetection() {
        this.isDetecting = true;
        this.detectPalm();
    }

    async detectPalm() {
        if (!this.isDetecting) return;
        try {
            await this.hands.send({ image: this.video });
        } catch (error) {
            console.error('Error in palm detection:', error);
        }
        requestAnimationFrame(() => this.detectPalm());
    }

    startScanEffect() {
        if (this.scanEffectInterval) return;
        const scanLine = document.getElementById('scan-line');
        if (!scanLine) return;
        scanLine.style.display = 'block';
        let pos = 0;
        let direction = 1;
        this.scanEffectInterval = setInterval(() => {
            pos += direction * 4;
            if (pos > this.canvas.height - 4) direction = -1;
            if (pos < 0) direction = 1;
            scanLine.style.top = pos + 'px';
        }, 10);
    }

    stopScanEffect() {
        if (this.scanEffectInterval) {
            clearInterval(this.scanEffectInterval);
            this.scanEffectInterval = null;
        }
        const scanLine = document.getElementById('scan-line');
        if (scanLine) scanLine.style.display = 'none';
    }

    onHandResults(results) {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        if (results.multiHandLandmarks.length > 0) {
            for (const landmarks of results.multiHandLandmarks) {
                this.drawLandmarks(landmarks);
            }
            const palmDetected = this.checkPalmPosition(results.multiHandLandmarks[0]);
            if (palmDetected && !this.palmDetected) {
                this.palmDetected = true;
                this.updateStatus('Palm detected! Scanning...');
                this.enableCapture();
                if (this.isPaymentScan) {
                    this.startScanEffect();
                    if (!this.autoScanTimeout) {
                        this.autoScanTimeout = setTimeout(() => {
                            this.capturePalm();
                        }, 2000);
                    }
                }
            } else if (!palmDetected && this.palmDetected) {
                this.palmDetected = false;
                this.updateStatus('Position your palm in the frame for detection.');
                this.disableCapture();
                if (this.isPaymentScan) {
                    this.stopScanEffect();
                    if (this.autoScanTimeout) {
                        clearTimeout(this.autoScanTimeout);
                        this.autoScanTimeout = null;
                    }
                }
            }
        } else {
            this.palmDetected = false;
            this.updateStatus('No palm detected. Position your palm in the frame.');
            this.disableCapture();
            if (this.isPaymentScan) {
                this.stopScanEffect();
                if (this.autoScanTimeout) {
                    clearTimeout(this.autoScanTimeout);
                    this.autoScanTimeout = null;
                }
            }
        }
    }

    drawLandmarks(landmarks) {
        this.ctx.strokeStyle = '#00FF00';
        this.ctx.lineWidth = 2;
        this.ctx.fillStyle = '#00FF00';
        const connections = [
            [0, 1], [1, 2], [2, 3], [3, 4],
            [0, 5], [5, 6], [6, 7], [7, 8],
            [0, 9], [9, 10], [10, 11], [11, 12],
            [0, 13], [13, 14], [14, 15], [15, 16],
            [0, 17], [17, 18], [18, 19], [19, 20],
            [0, 5], [5, 9], [9, 13], [13, 17]
        ];
        for (const [start, end] of connections) {
            const startPoint = landmarks[start];
            const endPoint = landmarks[end];
            this.ctx.beginPath();
            this.ctx.moveTo(startPoint.x * this.canvas.width, startPoint.y * this.canvas.height);
            this.ctx.lineTo(endPoint.x * this.canvas.width, endPoint.y * this.canvas.height);
            this.ctx.stroke();
        }
        for (const landmark of landmarks) {
            this.ctx.beginPath();
            this.ctx.arc(
                landmark.x * this.canvas.width,
                landmark.y * this.canvas.height,
                3, 0, 2 * Math.PI
            );
            this.ctx.fill();
        }
    }

    checkPalmPosition(landmarks) {
        const palmCenter = landmarks[9];
        const wrist = landmarks[0];
        const thumbTip = landmarks[4];
        const pinkyTip = landmarks[20];
        const centerX = palmCenter.x;
        const centerY = palmCenter.y;
        const isCentered = centerX > 0.3 && centerX < 0.7 && centerY > 0.3 && centerY < 0.7;
        const thumbPinkyDistance = Math.sqrt(
            Math.pow(thumbTip.x - pinkyTip.x, 2) + 
            Math.pow(thumbTip.y - pinkyTip.y, 2)
        );
        const isPalmOpen = thumbPinkyDistance > 0.3;
        const wristPalmDistance = Math.sqrt(
            Math.pow(wrist.x - palmCenter.x, 2) + 
            Math.pow(wrist.y - palmCenter.y, 2)
        );
        const isFacingCamera = wristPalmDistance > 0.1;
        return isCentered && isPalmOpen && isFacingCamera;
    }

    capturePalm() {
        if (this.isPaymentScan) {
            this.stopScanEffect();
            if (this.autoScanTimeout) {
                clearTimeout(this.autoScanTimeout);
                this.autoScanTimeout = null;
            }
        }
        if (!this.palmDetected) {
            this.updateStatus('Please position your palm properly before capturing.');
            return;
        }
        const captureCanvas = document.createElement('canvas');
        const captureCtx = captureCanvas.getContext('2d');
        captureCanvas.width = this.video.videoWidth;
        captureCanvas.height = this.video.videoHeight;
        captureCtx.drawImage(this.video, 0, 0);
        captureCanvas.toBlob((blob) => {
            this.capturedImage = blob;
            if (this.isPaymentScan && typeof window.showPalmUploadForm === 'function') {
                window.showPalmUploadForm(blob);
                this.updateStatus(' Palm captured! Submit for payment.');
            } else {
                const preview = document.getElementById('captured-palm-preview');
                if (preview) {
                    preview.src = URL.createObjectURL(blob);
                    preview.style.display = 'block';
                }
                const file = new File([blob], 'palm_capture.jpg', { type: 'image/jpeg' });
                const fileInput = document.getElementById('palm_image');
                if (fileInput) {
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(file);
                    fileInput.files = dataTransfer.files;
                }
                this.updateStatus('Palm captured successfully! You can now register.');
            }
            this.showRetakeButton();
            this.stopCamera();
        }, 'image/jpeg', 0.8);
    }

    retakePalm() {
        this.capturedImage = null;
        if (this.isPaymentScan) {
            document.getElementById('palm-upload-form').style.display = 'none';
            document.getElementById('scanned-palm-preview').style.display = 'none';
            document.getElementById('scanned_palm_image').value = '';
        } else {
            document.getElementById('captured-palm-preview').style.display = 'none';
            document.getElementById('palm_image').value = '';
        }
        this.updateStatus('Click "Start Camera" to capture palm again.');
        this.showStartButton();
    }

    stopCamera() {
        this.isDetecting = false;
        if (this.video.srcObject) {
            this.video.srcObject.getTracks().forEach(track => track.stop());
        }
        this.palmDetected = false;
    }

    updateStatus(message) {
        document.getElementById('palm-status-text').textContent = message;
    }

    showCaptureButton() {
        const startBtn = document.getElementById('start-camera-btn');
        const captureBtn = document.getElementById('capture-palm-btn');
        const retakeBtn = document.getElementById('retake-palm-btn');
        if (startBtn) startBtn.style.display = 'none';
        if (captureBtn) captureBtn.style.display = 'inline-block';
        if (retakeBtn) retakeBtn.style.display = 'none';
    }

    showRetakeButton() {
        const startBtn = document.getElementById('start-camera-btn');
        const captureBtn = document.getElementById('capture-palm-btn');
        const retakeBtn = document.getElementById('retake-palm-btn');
        if (startBtn) startBtn.style.display = 'none';
        if (captureBtn) captureBtn.style.display = 'none';
        if (retakeBtn) retakeBtn.style.display = 'inline-block';
    }

    showStartButton() {
        const startBtn = document.getElementById('start-camera-btn');
        const captureBtn = document.getElementById('capture-palm-btn');
        const retakeBtn = document.getElementById('retake-palm-btn');
        if (startBtn) startBtn.style.display = 'inline-block';
        if (captureBtn) captureBtn.style.display = 'none';
        if (retakeBtn) retakeBtn.style.display = 'none';
    }

    enableCapture() {
        const captureBtn = document.getElementById('capture-palm-btn');
        if (captureBtn) {
            captureBtn.disabled = false;
            captureBtn.textContent = 'Capture Palm';
        }
    }

    disableCapture() {
        const captureBtn = document.getElementById('capture-palm-btn');
        if (captureBtn) {
            captureBtn.disabled = true;
            captureBtn.textContent = 'Position Palm First';
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('camera-preview')) {
        window.palmDetector = new PalmDetector();
    }
});
