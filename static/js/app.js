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

  const avatar = document.createElement('div');
  avatar.className = 'message-avatar';
  avatar.innerText = '👤';

  const wrapper = document.createElement('div');
  wrapper.className = 'message-content-wrapper';

  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';
  bubble.innerHTML = formatResponseText(text);

  wrapper.appendChild(bubble);
  messageRow.appendChild(avatar);
  messageRow.appendChild(wrapper);
  messageList.appendChild(messageRow);

  scrollToBottom();
}

// Add bot message bubble
function addBotMessage(text, chips = []) {
  const messageList = document.getElementById('message-list');

  const messageRow = document.createElement('div');
  messageRow.className = 'message-row bot';

  const avatar = document.createElement('div');
  avatar.className = 'message-avatar';
  avatar.innerText = '🤖';

  const wrapper = document.createElement('div');
  wrapper.className = 'message-content-wrapper';

  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';
  bubble.innerHTML = formatResponseText(text);

  wrapper.appendChild(bubble);

  if (chips && chips.length > 0) {
    const chipsContainer = document.createElement('div');
    chipsContainer.className = 'chips-container';

    chips.forEach(chipText => {
      const chipBtn = document.createElement('button');
      chipBtn.className = 'chip-btn';
      chipBtn.innerText = chipText;
      chipBtn.addEventListener('click', () => {
        if (!isTyping) {
          sendMessage(chipText);
        }
      });
      chipsContainer.appendChild(chipBtn);
    });

    wrapper.appendChild(chipsContainer);
  }

  messageRow.appendChild(avatar);
  messageRow.appendChild(wrapper);
  messageList.appendChild(messageRow);

  scrollToBottom();
}

// Typing Indicator
function showTypingIndicator() {
  const messageList = document.getElementById('message-list');
  const id = 'typing-' + Date.now();

  const messageRow = document.createElement('div');
  messageRow.className = 'message-row bot';
  messageRow.id = id;

  const avatar = document.createElement('div');
  avatar.className = 'message-avatar';
  avatar.innerText = '🤖';

  const wrapper = document.createElement('div');
  wrapper.className = 'message-content-wrapper';

  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';

  const typingDots = document.createElement('div');
  typingDots.className = 'typing-dots';
  typingDots.innerHTML = '<span></span><span></span><span></span>';

  bubble.appendChild(typingDots);
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
function sendMessage(text, simulateOverride = false) {
  if (isTyping || !text.trim()) return;
  isTyping = true;

  const chatInput = document.getElementById('chat-input');
  const sendBtn = document.getElementById('send-btn');
  chatInput.disabled = true;
  sendBtn.classList.remove('enabled');

  addUserMessage(text);

  const typingId = showTypingIndicator();

  // Start background API call
  const isSimulation = simulateOverride || text.toLowerCase().trim() === 'simulate claude response';
  const chatPayload = {
    message: text,
    simulate_claude: isSimulation
  };

  fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(chatPayload)
  })
    .then(res => res.json())
    .then(backendData => {
      removeTypingIndicator(typingId);

      if (backendData.error === 'API_KEY_REQUIRED') {
        addBotMessage(backendData.response, ["Simulate Claude Response", "Back to main menu"]);
      } else {
        addBotMessage(backendData.response, backendData.chips || []);
      }

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

// Listeners config
window.addEventListener('DOMContentLoaded', () => {
  const chatInput = document.getElementById('chat-input');
  const sendBtn = document.getElementById('send-btn');

  chatInput.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
    if (this.scrollHeight > 100) {
      this.style.overflowY = 'auto';
    } else {
      this.style.overflowY = 'hidden';
    }

    if (this.value.trim().length > 0) {
      sendBtn.classList.add('enabled');
    } else {
      sendBtn.classList.remove('enabled');
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

  // Welcome message
  setTimeout(() => {
    const welcomeText = `👋 Hi! I'm **NexSupport** — your AI-powered customer service agent.\n\nI can help with:\n- 📦 **Order tracking & delivery**\n- 💳 **Refunds & billing**\n- 😤 **Complaints & escalations**\n- 🕐 **Support hours**`;
    const welcomeChips = ["Track my order", "I need a refund", "What are your hours?"];
    addBotMessage(welcomeText, welcomeChips);
  }, 400);
});
