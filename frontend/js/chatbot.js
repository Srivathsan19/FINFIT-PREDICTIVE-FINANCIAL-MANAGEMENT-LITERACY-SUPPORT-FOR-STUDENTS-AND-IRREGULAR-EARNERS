// Chatbot functionality

let chatbotOpen = false;
let chatbotWindow, chatbotToggle, chatbotClose, chatbotInput, chatbotSend, chatbotMessages;

function initChatbot() {
    chatbotWindow = document.getElementById('chatbot-window');
    chatbotToggle = document.getElementById('open-chatbot');
    chatbotClose = document.getElementById('close-chatbot');
    chatbotInput = document.getElementById('chatbot-input');
    chatbotSend = document.getElementById('send-chatbot');
    chatbotMessages = document.getElementById('chatbot-messages');
    
    if (chatbotToggle) {
        chatbotToggle.addEventListener('click', toggleChatbot);
    }
    if (chatbotClose) {
        chatbotClose.addEventListener('click', toggleChatbot);
    }
    if (chatbotSend) {
        chatbotSend.addEventListener('click', sendChatbotMessage);
    }
    if (chatbotInput) {
        chatbotInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendChatbotMessage();
            }
        });
    }
}

function toggleChatbot() {
    if (!chatbotWindow) return;
    chatbotOpen = !chatbotOpen;
    chatbotWindow.style.display = chatbotOpen ? 'flex' : 'none';
    if (chatbotOpen && chatbotInput) {
        chatbotInput.focus();
        scrollChatbotToBottom();
    }
}

function scrollChatbotToBottom() {
    if (!chatbotMessages) return;
    setTimeout(() => {
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }, 100);
}

function addMessage(text, isUser = false) {
    if (!chatbotMessages) return;
    const messageDiv = document.createElement('div');
    messageDiv.className = `chatbot-message ${isUser ? 'user-message' : 'bot-message'}`;
    
    if (isUser) {
        messageDiv.innerHTML = `
            <div class="message-content">
                <p>${escapeHtml(text)}</p>
            </div>
            <div class="message-avatar">👤</div>
        `;
    } else {
        // Format bot messages for better presentation
        const formattedText = formatBotMessage(text);
        messageDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content">
                ${formattedText}
            </div>
        `;
    }
    
    chatbotMessages.appendChild(messageDiv);
    scrollChatbotToBottom();
}

function addTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chatbot-message bot-message typing-indicator';
    typingDiv.id = 'typing-indicator';
    typingDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <div class="typing-dots">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    chatbotMessages.appendChild(typingDiv);
    scrollChatbotToBottom();
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) indicator.remove();
}

async function sendChatbotMessage() {
    if (!chatbotInput) return;
    const msg = chatbotInput.value.trim();
    if (!msg) return;
    
    // Add user message
    addMessage(msg, true);
    chatbotInput.value = '';
    
    // Show typing indicator
    addTypingIndicator();
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: msg})
        });
        
        const data = await response.json();
        removeTypingIndicator();
        
        if (data.reply) {
            addMessage(data.reply, false);
        } else {
            addMessage('Sorry, I encountered an error. Please try again.', false);
        }
    } catch (error) {
        removeTypingIndicator();
        addMessage('Unable to connect to the assistant. Please check if Ollama is running on localhost:11434', false);
        console.error('Chatbot error:', error);
    }
}

