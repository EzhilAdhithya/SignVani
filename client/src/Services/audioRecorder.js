/**
 * Enhanced Audio Recorder for SignVani
 * Records audio and sends to backend for processing
 */

class AudioRecorder {
  constructor() {
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.stream = null;
    this.isRecording = false;
    this.onTranscript = null;
    this.onError = null;
    this.onProcessingStart = null;
    this.onProcessingEnd = null;
  }

  /**
   * Initialize audio recorder
   * @param {Object} options - Configuration options
   */
  async initialize(options = {}) {
    try {
      this.onTranscript = options.onTranscript;
      this.onError = options.onError;
      this.onProcessingStart = options.onProcessingStart;
      this.onProcessingEnd = options.onProcessingEnd;

      // Request microphone access
      this.stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000,
          channelCount: 1
        } 
      });

      // Create media recorder
      this.mediaRecorder = new MediaRecorder(this.stream, {
        mimeType: 'audio/webm;codecs=opus'
      });

      // Setup event handlers
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

      this.mediaRecorder.onstop = async () => {
        await this.processAudio();
      };

      console.log('Audio recorder initialized successfully');
      return true;
    } catch (error) {
      console.error('Failed to initialize audio recorder:', error);
      if (this.onError) {
        this.onError('Failed to access microphone. Please check permissions.');
      }
      return false;
    }
  }

  /**
   * Start recording
   */
  startRecording() {
    if (!this.mediaRecorder) {
      if (this.onError) {
        this.onError('Audio recorder not initialized');
      }
      return;
    }

    if (this.isRecording) {
      console.warn('Recording already in progress');
      return;
    }

    this.audioChunks = [];
    this.mediaRecorder.start();
    this.isRecording = true;
    console.log('Recording started');
  }

  /**
   * Stop recording
   */
  stopRecording() {
    if (!this.isRecording) {
      console.warn('No recording in progress');
      return;
    }

    this.mediaRecorder.stop();
    this.isRecording = false;
    console.log('Recording stopped');
  }

  /**
   * Process recorded audio and send to backend
   */
  async processAudio() {
    if (this.audioChunks.length === 0) {
      console.warn('No audio data to process');
      return;
    }

    try {
      if (this.onProcessingStart) {
        this.onProcessingStart();
      }

      // Create audio blob
      const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
      
      // Convert to WAV format for backend compatibility
      const wavBlob = await this.convertToWav(audioBlob);
      
      // Send to backend
      const apiService = (await import('./apiService')).default;
      const result = await apiService.speechToSign(wavBlob);

      if (this.onTranscript) {
        this.onTranscript(result);
      }

    } catch (error) {
      console.error('Error processing audio:', error);
      if (this.onError) {
        this.onError('Failed to process audio. Please try again.');
      }
    } finally {
      if (this.onProcessingEnd) {
        this.onProcessingEnd();
      }
    }
  }

  /**
   * Convert WebM blob to WAV format
   * @param {Blob} webmBlob - WebM audio blob
   * @returns {Promise<Blob>} - WAV audio blob
   */
  async convertToWav(webmBlob) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = async () => {
        try {
          // For now, we'll send the WebM blob directly
          // In a production environment, you might want to convert to WAV
          // using Web Audio API or a library like lamejs
          resolve(webmBlob);
        } catch (error) {
          reject(error);
        }
      };
      
      reader.onerror = () => reject(new Error('Failed to read audio blob'));
      reader.readAsArrayBuffer(webmBlob);
    });
  }

  /**
   * Clean up resources
   */
  cleanup() {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
    
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.isRecording = false;
  }

  /**
   * Check if recording is in progress
   */
  isCurrentlyRecording() {
    return this.isRecording;
  }
}

export default AudioRecorder;
