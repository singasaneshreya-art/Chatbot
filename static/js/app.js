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
