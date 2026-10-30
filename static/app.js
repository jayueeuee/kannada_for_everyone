/**
 * Kannada for Everyone - Client-Side Helper Scripts
 * Handles speech synthesis fallback, copy-to-clipboard, and audio triggers.
 */

window.KFE = {
  speakKannada: function (text) {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'kn-IN';
      utterance.rate = 0.85; // Slower pace suitable for beginners
      window.speechSynthesis.speak(utterance);
    } else {
      console.warn('Speech synthesis not supported in this browser.');
    }
  },

  copyText: function (text) {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(function() {
        console.log('Copied to clipboard:', text);
      });
    }
  }
};
