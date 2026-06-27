// State Variables
let isTyping = false;

// Format Markdown Bold, Code, Newline tags
function formatResponseText(text) {
  if (!text) return "";
  let formatted = text;

  formatted = formatted
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  formatted = formatted.replace(/`(.*?)`/g, '<code>$1</code>');
  formatted = formatted.replace(/\n/g, '<br>');

  return formatted;
}

// Add user message bubble
function addUserMessage(text) {
  const messageList = document.getElementById('message-list');

  const messageRow = document.createElement('div');
  messageRow.className = 'message-row user';

  const wrapper = document.createElement('div');
  wrapper.className = 'message-content-wrapper';

  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';
  bubble.innerHTML = formatResponseText(text);

  wrapper.appendChild(bubble);
  messageRow.appendChild(wrapper);
  messageList.appendChild(messageRow);

  scrollToBottom();
}

// Render dynamic action chips in the footer
function renderChips(chips = []) {
  const chipsContainer = document.getElementById('chips-container');
  chipsContainer.innerHTML = '';

  if (!chips || chips.length === 0) return;

  chips.forEach(chipText => {
    const chipBtn = document.createElement('button');
    chipBtn.className = 'chip-btn';
    
    // Add custom classes and icons based on chip labels to match mockup design
    if (chipText.toLowerCase().includes('track gps')) {
      chipBtn.classList.add('action-primary');
      chipBtn.innerHTML = `
        <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm0-10c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
        </svg>
        <span>${chipText}</span>
      `;
    } else if (chipText.toLowerCase().includes('contact')) {
      chipBtn.classList.add('action-primary');
      chipBtn.innerHTML = `
        <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
          <path d="M20.01 15.38c-1.23 0-2.42-.2-3.53-.57a.977.977 0 0 0-1.01.24l-2.2 2.2a15.045 15.045 0 0 1-6.59-6.59l2.2-2.2a.96.96 0 0 0 .25-1.02c-.37-1.11-.57-2.3-.57-3.53C9 3.5 8.5 3 7.88 3H4.03C3.5 3 3 3.5 3 4.03c0 9.37 7.6 16.97 16.97 16.97.53 0 1.03-.5 1.03-1.03v-3.88c0-.62-.5-1.12-1.12-1.12z"/>
        </svg>
        <span>${chipText}</span>
      `;
    } else if (chipText.toLowerCase().includes('refund')) {
      chipBtn.classList.add('action-secondary');
      chipBtn.innerText = chipText;
    } else {
      chipBtn.innerText = chipText;
    }

    chipBtn.addEventListener('click', () => {
      if (!isTyping) {
        sendMessage(chipText);
      }
    });

    chipsContainer.appendChild(chipBtn);
  });
}

// Add bot message bubble
function addBotMessage(text, chips = [], orderCard = null) {
  const messageList = document.getElementById('message-list');

  const messageRow = document.createElement('div');
  messageRow.className = 'message-row bot';

  // Bot Avatar (dark circle)
  const avatar = document.createElement('div');
  avatar.className = 'bot-avatar-icon';

  const wrapper = document.createElement('div');
  wrapper.className = 'message-content-wrapper';

  // Bot Header (Name + Status Dot)
  const header = document.createElement('div');
  header.className = 'bot-name-row';
  header.innerHTML = `<span>Support AI</span><span class="bot-dot">●</span>`;
  wrapper.appendChild(header);

  // Bubble Content
  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';
  bubble.innerHTML = formatResponseText(text);
  wrapper.appendChild(bubble);

  // Render Order Card if metadata is present
  if (orderCard) {
    const cardEl = document.createElement('div');
    cardEl.className = 'order-card';
    cardEl.innerHTML = `
      <div class="order-card-header">
        <span class="order-card-title">Order Summary</span>
        <span class="order-card-badge">${orderCard.badge || 'Active Dispute'}</span>
      </div>
      <div class="order-card-body">
        <img class="order-card-img" src="${orderCard.image || '/static/images/chair.png'}" alt="${orderCard.item}">
        <div class="order-card-info">
          <span class="order-card-name">${orderCard.item}</span>
          <span class="order-card-model">${orderCard.model || ''}</span>
          <span class="order-card-price">${orderCard.price}</span>
        </div>
      </div>
    `;
    bubble.appendChild(cardEl);
  }

  messageRow.appendChild(avatar);
  messageRow.appendChild(wrapper);
  messageList.appendChild(messageRow);

  // Render action chips in the footer area
  renderChips(chips);
  scrollToBottom();
}

// Typing Indicator matching mockup style
function showTypingIndicator() {
  const messageList = document.getElementById('message-list');
  const id = 'typing-' + Date.now();

  const messageRow = document.createElement('div');
  messageRow.className = 'message-row bot';
  messageRow.id = id;

  const avatar = document.createElement('div');
  avatar.className = 'bot-avatar-icon';

  const wrapper = document.createElement('div');
  wrapper.className = 'message-content-wrapper';

  const header = document.createElement('div');
  header.className = 'bot-name-row';
  header.innerHTML = `<span>Support AI</span><span class="bot-dot">●</span>`;
  wrapper.appendChild(header);

  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';

  const typingDotsText = document.createElement('div');
  typingDotsText.className = 'typing-row-text';
  typingDotsText.innerHTML = `
    <span class="dots"><span></span><span></span><span></span></span>
    <span>AI is investigating...</span>
  `;

  bubble.appendChild(typingDotsText);
  wrapper.appendChild(bubble);
  messageRow.appendChild(avatar);
  messageRow.appendChild(wrapper);
  messageList.appendChild(messageRow);

  scrollToBottom();
  return id;
}

// Remove typing indicator
function removeTypingIndicator(id) {
  const indicator = document.getElementById(id);
  if (indicator) {
    indicator.remove();
  }
}

// Scroll main container to bottom
function scrollToBottom() {
  const chatMain = document.querySelector('.chat-main');
  chatMain.scrollTo({
    top: chatMain.scrollHeight,
    behavior: 'smooth'
  });
}

// Primary send message function
function sendMessage(text) {
  if (isTyping || !text.trim()) return;
  isTyping = true;

  const chatInput = document.getElementById('chat-input');
  chatInput.disabled = true;

  addUserMessage(text);

  // Clear footer chips while bot is typing
  renderChips([]);

  const typingId = showTypingIndicator();

  fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ message: text })
  })
    .then(res => res.json())
    .then(backendData => {
      removeTypingIndicator(typingId);

      addBotMessage(
        backendData.response, 
        backendData.chips || [], 
        backendData.order_card || null
      );

      chatInput.disabled = false;
      chatInput.value = '';
      chatInput.style.height = '24px';
      isTyping = false;
      chatInput.focus();
    })
    .catch(err => {
      console.error(err);
      removeTypingIndicator(typingId);
      addBotMessage("⚠️ **Error**: Failed to connect to chatbot backend server. Please verify app.py is active.", ["Retry"]);
      chatInput.disabled = false;
      isTyping = false;
    });
}

// Language Selector Logic (Synchronized with Python Backend)
function initLanguageSelector() {
  const selector = document.getElementById('language-selector');
  const btn = document.getElementById('language-btn');
  const dropdown = document.getElementById('language-dropdown');
  const label = document.getElementById('language-label');

  if (!selector || !btn || !dropdown || !label) return;

  // Load language preference from global config set by backend
  const activeLang = window.APP_CONFIG?.activeLanguage || 'en';
  localStorage.setItem('supportai-language', activeLang);
  
  const savedOption = dropdown.querySelector(`[data-lang="${activeLang}"]`);
  if (savedOption) {
    label.textContent = savedOption.textContent;
    dropdown.querySelectorAll('.language-option').forEach(opt => opt.classList.remove('active'));
    savedOption.classList.add('active');
  }

  // Toggle dropdown
  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    selector.classList.toggle('open');
  });

  // Handle language option click
  dropdown.querySelectorAll('.language-option').forEach(option => {
    option.addEventListener('click', (e) => {
      e.stopPropagation();
      const lang = option.getAttribute('data-lang');
      
      // Update language on Python backend
      fetch('/api/language', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ language: lang })
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          localStorage.setItem('supportai-language', lang);
          // Reload the page to load translation assets/welcome messages
          window.location.reload();
        }
      })
      .catch(err => {
        console.error("Error setting language on backend:", err);
      });

      selector.classList.remove('open');
    });
  });

  // Close dropdown when clicking outside
  document.addEventListener('click', (e) => {
    if (!selector.contains(e.target)) {
      selector.classList.remove('open');
    }
  });
}

// Listeners config
window.addEventListener('DOMContentLoaded', () => {
  const chatInput = document.getElementById('chat-input');
  const sendBtn = document.getElementById('send-btn');

  chatInput.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
    if (this.scrollHeight > 80) {
      this.style.overflowY = 'auto';
    } else {
      this.style.overflowY = 'hidden';
    }
  });

  chatInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (this.value.trim().length > 0 && !isTyping) {
        sendMessage(this.value.trim());
      }
    }
  });

  sendBtn.addEventListener('click', () => {
    if (chatInput.value.trim().length > 0 && !isTyping) {
      sendMessage(chatInput.value.trim());
    }
  });

  // Sidebar new chat trigger
  const newChatBtn = document.getElementById('new-chat-btn');
  if (newChatBtn) {
    newChatBtn.addEventListener('click', () => {
      fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: 'back' })
      }).then(() => {
        document.getElementById('message-list').innerHTML = '';
        document.getElementById('chips-container').innerHTML = '';
        const welcomeText = window.APP_CONFIG?.welcomeText || `👋 Hi! I'm **Support AI** — your AI-powered customer service agent.\n\nI can help you track your **order**, process a **refund**, or check our **support hours**! What can I do for you today?`;
        const welcomeChips = window.APP_CONFIG?.welcomeChips || ["Track my order", "I need a refund", "What are your hours?"];
        addBotMessage(welcomeText, welcomeChips);
      });
    });
  }

  // Initialize language selector
  initLanguageSelector();

  // Show welcome message on startup
  const welcomeText = window.APP_CONFIG?.welcomeText || `👋 Hi! I'm **Support AI** — your AI-powered customer service agent.\n\nI can help you track your **order**, process a **refund**, or check our **support hours**! What can I do for you today?`;
  const welcomeChips = window.APP_CONFIG?.welcomeChips || ["Track my order", "I need a refund", "What are your hours?"];
  addBotMessage(welcomeText, welcomeChips);
});

// ─────────────────────────────────────────────────────────────────────────────
// Speech-to-Text via Web Speech API
// Drop this block at the bottom of your existing app.js (before any closing
// DOMContentLoaded wrapper if one exists, or just appended to the file).
// ─────────────────────────────────────────────────────────────────────────────

(function () {
  // ── 1. Browser support check ──────────────────────────────────────────────
  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

  const micBtn   = document.getElementById('mic-btn');
  const chatInput = document.getElementById('chat-input');

  if (!micBtn) return; // guard: element not found

  if (!SpeechRecognition) {
    // Graceful degradation: hide or visually disable the button
    micBtn.setAttribute('title', 'Speech recognition is not supported in this browser. Try Chrome or Edge.');
    micBtn.style.opacity = '0.4';
    micBtn.style.cursor  = 'not-allowed';
    micBtn.addEventListener('click', function (e) {
      e.preventDefault();
      alert('🎤 Speech recognition is not supported in this browser.\nPlease use Google Chrome, Microsoft Edge, or Safari.');
    });
    return;
  }

  // ── 2. Language map ───────────────────────────────────────────────────────
  // Maps your app's short language codes to BCP-47 locales for the Speech API.
  // Extend this object if you add more languages to the session manager.
  const LANG_MAP = {
    'en': 'en-US',
    'hi': 'hi-IN',
    'mr': 'mr-IN',
    'ta': 'ta-IN',
    'te': 'te-IN',
    'kn': 'kn-IN',
    'gu': 'gu-IN',
    'bn': 'bn-IN',
    'pa': 'pa-IN',
    'fr': 'fr-FR',
    'de': 'de-DE',
    'es': 'es-ES',
    'zh': 'zh-CN',
    'ja': 'ja-JP',
    'ar': 'ar-SA',
  };

  /**
   * Reads the active language from the DOM.
   * Looks for the data-lang attribute on the active language-option button,
   * or falls back to the <html lang> attribute, then 'en'.
   */
  function getActiveLang() {
    // Match the actual DOM: <button class="language-option active" data-lang="hi">
    const activeBtn = document.querySelector('.language-option.active[data-lang]');
    if (activeBtn) {
      const code = activeBtn.getAttribute('data-lang');
      if (code) return LANG_MAP[code] || code;
    }
    // Fallback to <html lang="...">
    const htmlLang = document.documentElement.lang;
    if (htmlLang) return LANG_MAP[htmlLang] || htmlLang;
    return 'en-US';
  }

  // ── 3. Recognition setup ──────────────────────────────────────────────────
  let recognition = null;
  let isRecording = false;

  function buildRecognition() {
    const rec = new SpeechRecognition();
    rec.lang            = getActiveLang();
    rec.interimResults  = true;   // stream partial transcripts for live preview
    rec.continuous      = false;  // stop after the first natural pause
    rec.maxAlternatives = 1;

    // ── onresult: insert transcript into the textarea ──────────────────────
    rec.onresult = function (event) {
      let interimText = '';
      let finalText   = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalText += transcript;
        } else {
          interimText += transcript;
        }
      }

      if (finalText) {
        // Append final text (with a space if the box already has content)
        const current = chatInput.value.trimEnd();
        chatInput.value = current ? current + ' ' + finalText.trim() : finalText.trim();
        chatInput.dispatchEvent(new Event('input')); // trigger any existing auto-resize
      } else if (interimText) {
        // Show interim result as placeholder so the user sees live feedback
        chatInput.setAttribute('placeholder', '🎤 ' + interimText + '…');
      }
    };

    // ── onerror: reset UI and surface user-friendly messages ───────────────
    rec.onerror = function (event) {
      const messages = {
        'no-speech':         'No speech detected. Please try again.',
        'audio-capture':     'Microphone not found. Check your device settings.',
        'not-allowed':       'Microphone access was denied. Please allow access in your browser settings.',
        'network':           'A network error occurred during recognition.',
        'aborted':           null, // user-cancelled, no message needed
        'service-not-allowed': 'Speech service is not allowed. Try using HTTPS.',
      };
      const msg = messages[event.error];
      if (msg) {
        console.warn('[Speech] Error:', event.error, msg);
        // Non-intrusive: show briefly in the placeholder
        chatInput.setAttribute('placeholder', '⚠️ ' + msg);
        setTimeout(() => restorePlaceholder(), 4000);
      }
      stopRecording();
    };

    // ── onend: always reset UI when recognition stops ─────────────────────
    rec.onend = function () {
      stopRecording();
    };

    return rec;
  }

  // ── 4. State management ───────────────────────────────────────────────────
  const originalPlaceholder = chatInput ? (chatInput.getAttribute('placeholder') || 'Type a message…') : '';

  function restorePlaceholder() {
    if (chatInput) chatInput.setAttribute('placeholder', originalPlaceholder);
  }

  function startRecording() {
    recognition = buildRecognition();
    isRecording = true;
    micBtn.classList.add('recording');
    micBtn.setAttribute('aria-label', 'Stop recording');
    micBtn.setAttribute('title', 'Click to stop recording');
    if (chatInput) chatInput.setAttribute('placeholder', '🎤 Listening…');
    recognition.start();
  }

  function stopRecording() {
    isRecording = false;
    micBtn.classList.remove('recording');
    micBtn.setAttribute('aria-label', 'Start voice input');
    micBtn.setAttribute('title', 'Click to speak');
    restorePlaceholder();
    if (recognition) {
      try { recognition.stop(); } catch (_) { /* already stopped */ }
      recognition = null;
    }
  }

  // ── 5. Mic button click handler ───────────────────────────────────────────
  micBtn.addEventListener('click', function (e) {
    e.preventDefault();
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  });

  // ── 6. Keyboard accessibility ─────────────────────────────────────────────
  micBtn.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      micBtn.click();
    }
  });

})();
