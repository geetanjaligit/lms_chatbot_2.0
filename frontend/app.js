document.addEventListener('DOMContentLoaded', function () {
    const toggleSidebarButton = document.getElementById('toggle-sidebar');
    const sidebar = document.querySelector('.sidebar');
    const searchChatBtn = document.getElementById('search-chat-btn');
    const chatSearchInput = document.getElementById('chat-search-input');
    const chatsList = document.getElementById('chats-list');
    const noChatsMessage = document.getElementById('no-chats');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const chatArea = document.getElementById('chat-area');
    const roleSelectBtn = document.getElementById('role-select-btn');
    const roleDialog = document.getElementById('role-dialog');
    const selectRoleConfirm = document.getElementById('select-role-confirm');
    const attachFileBtn = document.getElementById('attach-file-btn');
    const fileInput = document.getElementById('file-input');
    const voiceRecordBtn = document.getElementById('voice-record-btn');
    const newChatBtn = document.getElementById('new-chat-btn');
    const filePreviews = document.getElementById('file-previews');
    const contextMenu = document.getElementById('context-menu');
    const renameChatBtn = document.getElementById('rename-chat');
    const deleteChatBtn = document.getElementById('delete-chat');

    let chats = JSON.parse(localStorage.getItem('lms_chats')) || [];
    let currentChatId = localStorage.getItem('lms_current_chat_id') || null;
    let contextMenuChatId = null;
    let selectedFiles = [];

    // --- File Attachment Logic ---
    attachFileBtn.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', () => {
        const files = Array.from(fileInput.files);
        files.forEach(file => {
            if (!selectedFiles.some(f => f.name === file.name && f.size === file.size)) {
                selectedFiles.push(file);
            }
        });
        renderFilePreviews();
        fileInput.value = ''; // Reset to allow re-selecting same file
    });

    function renderFilePreviews() {
        filePreviews.innerHTML = '';
        selectedFiles.forEach((file, index) => {
            const chip = document.createElement('div');
            chip.className = 'file-preview-chip';
            chip.innerHTML = `
                <span>${file.name}</span>
                <span class="remove-file" data-index="${index}">
                    <span class="iconify" data-icon="ph:x-circle"></span>
                </span>
            `;
            filePreviews.appendChild(chip);
        });

        document.querySelectorAll('.remove-file').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.currentTarget.dataset.index);
                selectedFiles.splice(index, 1);
                renderFilePreviews();
            });
        });
    }

    // --- Chat History Logic ---

    function saveToLocalStorage() {
        localStorage.setItem('lms_chats', JSON.stringify(chats));
        localStorage.setItem('lms_current_chat_id', currentChatId);
    }

    function renderChats() {
        chatsList.innerHTML = '';
        const searchTerm = chatSearchInput.value.toLowerCase();

        const filteredChats = chats.filter(chat =>
            chat.title.toLowerCase().includes(searchTerm)
        );

        if (filteredChats.length === 0) {
            noChatsMessage.style.display = 'flex';
            chatsList.style.display = 'none';
        } else {
            noChatsMessage.style.display = 'none';
            chatsList.style.display = 'flex';

            filteredChats.forEach(chat => {
                const li = document.createElement('li');
                li.className = 'chat-list-item';
                if (chat.id === currentChatId) li.classList.add('active');
                li.textContent = chat.title;

                // Left click to switch
                li.addEventListener('click', () => switchChat(chat.id));

                // Right click for context menu
                li.addEventListener('contextmenu', (e) => {
                    e.preventDefault();
                    showContextMenu(e, chat.id);
                });

                chatsList.appendChild(li);
            });
        }
    }

    function showContextMenu(e, chatId) {
        contextMenuChatId = chatId;
        contextMenu.style.display = 'block';
        contextMenu.style.left = `${e.pageX}px`;
        contextMenu.style.top = `${e.pageY}px`;
    }

    function hideContextMenu() {
        contextMenu.style.display = 'none';
        contextMenuChatId = null;
    }

    function renameChat() {
        if (!contextMenuChatId) return;
        const chat = chats.find(c => c.id === contextMenuChatId);
        if (!chat) return;

        const newTitle = prompt('Enter new chat title:', chat.title);
        if (newTitle && newTitle.trim() !== '') {
            chat.title = newTitle.trim();
            saveToLocalStorage();
            renderChats();
        }
        hideContextMenu();
    }

    function deleteChat() {
        if (!contextMenuChatId) return;
        if (!confirm('Are you sure you want to delete this chat?')) {
            hideContextMenu();
            return;
        }

        chats = chats.filter(c => c.id !== contextMenuChatId);

        if (currentChatId === contextMenuChatId) {
            currentChatId = chats.length > 0 ? chats[0].id : null;
            loadCurrentChat();
        }

        saveToLocalStorage();
        renderChats();
        hideContextMenu();
    }

    function createNewChat() {
        const newChat = {
            id: Date.now().toString(),
            title: 'New Chat',
            messages: []
        };
        chats.unshift(newChat);
        currentChatId = newChat.id;
        saveToLocalStorage();
        renderChats();
        loadCurrentChat();
        if (window.innerWidth <= 768) sidebar.classList.remove('open');
    }

    function switchChat(id) {
        currentChatId = id;
        saveToLocalStorage();
        renderChats();
        loadCurrentChat();
        if (window.innerWidth <= 768) sidebar.classList.remove('open');
    }

    function loadCurrentChat() {
        chatArea.innerHTML = '';
        const currentChat = chats.find(c => c.id === currentChatId);

        if (!currentChat || currentChat.messages.length === 0) {
            const welcome = document.createElement('div');
            welcome.className = 'welcome-message';
            welcome.id = 'welcome-message';
            welcome.innerHTML = '<h1>Hi, how can I assist you today?</h1>';
            chatArea.appendChild(welcome);
        } else {
            currentChat.messages.forEach(msg => {
                displayMessage(msg.text, msg.role);
            });
        }
        chatArea.scrollTop = chatArea.scrollHeight;
    }

    function displayMessage(text, role) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${role}-message`;

        if (role === 'bot') {
            // Use marked to parse markdown for bot messages
            messageDiv.innerHTML = typeof marked !== 'undefined' ? marked.parse(text) : text;
        } else {
            messageDiv.textContent = text;
        }

        chatArea.appendChild(messageDiv);
        chatArea.scrollTop = chatArea.scrollHeight;
        return messageDiv;
    }

    newChatBtn.addEventListener('click', (e) => {
        e.preventDefault();
        createNewChat();
    });

    renameChatBtn.addEventListener('click', renameChat);
    deleteChatBtn.addEventListener('click', deleteChat);

    document.addEventListener('click', () => {
        hideContextMenu();
    });

    // Sidebar Toggle
    toggleSidebarButton.addEventListener('click', function () {
        if (window.innerWidth <= 768) {
            sidebar.classList.toggle('open');
        } else {
            sidebar.classList.toggle('collapsed');
        }
    });

    // Chat Search
    searchChatBtn.addEventListener('click', function () {
        chatSearchInput.classList.toggle('visible');
        if (chatSearchInput.classList.contains('visible')) {
            chatSearchInput.focus();
        }
    });

    chatSearchInput.addEventListener('keyup', renderChats);

    // Role Selection Dialog
    let currentRole = 'student'; // Default role

    function updateEmailDisplay() {
        const storedUser = localStorage.getItem('lms_user') || 'User';
        const domain = currentRole === 'faculty' ? 'faculty.sharda.ac.in' : 'student.sharda.ac.in';
        displayEmail.textContent = `${storedUser.toLowerCase().replace(/\s+/g, '')}@${domain}`;
    }

    roleSelectBtn.addEventListener('click', function (event) {
        event.stopPropagation();
        roleDialog.classList.toggle('visible');
    });

    selectRoleConfirm.addEventListener('click', function () {
        const selectedRadio = document.querySelector('input[name="role"]:checked');
        if (selectedRadio) {
            currentRole = selectedRadio.value;
            updateEmailDisplay();

            // Visual feedback
            const icon = roleSelectBtn.querySelector('.iconify');
            if (currentRole === 'faculty') {
                icon.setAttribute('data-icon', 'ph:chalkboard-teacher-fill');
            } else {
                icon.setAttribute('data-icon', 'ph:student-fill');
            }
        }
        roleDialog.classList.remove('visible');
    });

    document.addEventListener('click', function (event) {
        if (!roleDialog.contains(event.target) && !roleSelectBtn.contains(event.target)) {
            roleDialog.classList.remove('visible');
        }
    });

    // File Attachment
    attachFileBtn.addEventListener('click', function () {
        fileInput.click();
    });

    fileInput.addEventListener('change', function () {
        if (fileInput.files.length > 0) {
            console.log('File selected:', fileInput.files[0].name);
        }
    });

    // Voice Recording
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition;
    let isRecording = false;
    let finalTranscript = '';

    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = true; // Keep recording until stopped manually
        recognition.interimResults = true; // Show results as they come
        recognition.lang = 'en-US';

        voiceRecordBtn.addEventListener('click', () => {
            if (isRecording) {
                recognition.stop();
            } else {
                finalTranscript = ''; // Reset for new recording
                try {
                    recognition.start();
                } catch (err) {
                    console.error('Speech recognition start error:', err);
                    isRecording = false;
                    updateVoiceUI(false);
                }
            }
        });

        recognition.onstart = () => {
            isRecording = true;
            updateVoiceUI(true);
            chatInput.placeholder = 'Listening... (Click tick to stop)';
        };

        recognition.onresult = (event) => {
            let interimTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }
            chatInput.value = finalTranscript + interimTranscript;
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            if (event.error === 'not-allowed') {
                alert('Microphone access denied. Please check your browser settings.');
                if (navigator.userAgent.includes("Brave")) {
                    alert('Brave users: Please enable "Google Services for Push Messaging and Web Speech API" in Brave Settings -> Privacy and security.');
                }
            }
            isRecording = false;
            updateVoiceUI(false);
        };

        recognition.onend = () => {
            isRecording = false;
            updateVoiceUI(false);
            chatInput.placeholder = 'Type something...';
        };

        function updateVoiceUI(recording) {
            const icon = voiceRecordBtn.querySelector('.iconify');
            if (recording) {
                voiceRecordBtn.classList.add('recording');
                if (icon) icon.setAttribute('data-icon', 'ph:check-circle-fill');
            } else {
                voiceRecordBtn.classList.remove('recording');
                if (icon) icon.setAttribute('data-icon', 'ph:microphone');
            }
        }

    } else {
        voiceRecordBtn.disabled = true;
        const msg = 'Speech recognition not supported in this browser.';
        voiceRecordBtn.title = msg;
        if (navigator.userAgent.includes("Brave")) {
            console.log(msg + ' (Brave users may need to enable Google Services in settings)');
        }
    }

    // Chat Functionality
    async function sendMessage() {
        const messageText = chatInput.value.trim();
        if (messageText === '' && selectedFiles.length === 0) return;

        if (!currentChatId) {
            createNewChat();
        }

        const currentChat = chats.find(c => c.id === currentChatId);

        // Update title if it's the first message
        if (currentChat.messages.length === 0) {
            const titleText = messageText || (selectedFiles.length > 0 ? selectedFiles[0].name : 'New Chat');
            currentChat.title = titleText.substring(0, 30) + (titleText.length > 30 ? '...' : '');
            renderChats();
        }

        // Hide welcome message if present
        const welcome = document.getElementById('welcome-message');
        if (welcome) welcome.style.display = 'none';

        // Display user message
        displayMessage(messageText || (selectedFiles.length > 0 ? `Sent ${selectedFiles.length} file(s)` : ""), 'user');
        currentChat.messages.push({ role: 'user', text: messageText });

        chatInput.value = '';

        // Create a placeholder for the bot's response
        const botMessageDiv = displayMessage('Thinking...', 'bot');
        botMessageDiv.innerHTML = '<span class="iconify" data-icon="eos-icons:bubble-loading"></span> Thinking...';

        try {
            const formData = new FormData();
            formData.append('query', messageText);
            selectedFiles.forEach(file => {
                formData.append('files', file);
            });

            const token = localStorage.getItem('lms_token');
            if (!token) {
                window.location.href = 'login.html';
                return;
            }

            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    query: messageText,
                    role: currentRole
                })
            });

            if (response.status === 401) {
                alert('Session expired. Please login again.');
                localStorage.removeItem('lms_token');
                window.location.href = 'login.html';
                return;
            }

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            const answer = data.answer || 'No answer received.';
            const sources = data.sources_retrieved || 0;
            const dataSources = data.data_sources || [];
            const confidence = data.confidence || 'unknown';

            // Create enhanced response with metadata
            let responseHtml = '';
            if (typeof marked !== 'undefined') {
                responseHtml = marked.parse(answer);
            } else {
                responseHtml = answer.replace(/\n/g, '<br>');
            }

            // Add source information if available
            if (sources > 0) {
                responseHtml += `
                    <div class="response-metadata">
                        <hr style="margin: 15px 0; border: none; border-top: 1px solid #eee;">
                        <div class="metadata-info">
                            <span class="iconify" data-icon="ph:info-circle" style="color: #666;"></span>
                            <small style="color: #666;">
                                Retrieved ${sources} sources${dataSources.length > 0 ? ' from: ' + dataSources.join(', ') : ''}
                                ${confidence === 'high' ? ' • High confidence' : ''}
                            </small>
                        </div>
                    </div>
                `;
            }

            botMessageDiv.innerHTML = responseHtml;
            currentChat.messages.push({ role: 'bot', text: answer });

            // Clear files after successful send
            selectedFiles = [];
            renderFilePreviews();
        } catch (error) {
            console.error('Error:', error);
            const errorMsg = 'Error: Could not connect to the server. Please ensure app_rag.py is running.';
            botMessageDiv.textContent = errorMsg;
            botMessageDiv.style.color = '#ff4444';
            currentChat.messages.push({ role: 'bot', text: errorMsg });
        }

        saveToLocalStorage();
    }

    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            sendMessage();
        }
    });

    // Responsive Handling
    function handleResize() {
        if (window.innerWidth > 768) {
            sidebar.classList.remove('open');
        }
    }

    // --- Dynamic User Profile & Dropdown ---
    const userProfileBtn = document.getElementById('user-profile-btn');
    const userDropdown = document.getElementById('user-dropdown');
    const logoutOption = document.getElementById('logout-option');
    const displayUsername = document.getElementById('display-username');
    const displayEmail = document.getElementById('display-email');

    // Populate User Info
    const storedUser = localStorage.getItem('lms_user');
    if (storedUser) {
        displayUsername.textContent = storedUser;
        updateEmailDisplay(); // Initial load
    }

    // Toggle Dropdown
    if (userProfileBtn && userDropdown) {
        userProfileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            // Toggle visibility
            const isVisible = userDropdown.style.display === 'block';
            userDropdown.style.display = isVisible ? 'none' : 'block';

            // Position above the profile
            if (!isVisible) {
                const rect = userProfileBtn.getBoundingClientRect();
                userDropdown.style.bottom = (window.innerHeight - rect.top + 10) + 'px';
                userDropdown.style.left = rect.left + 'px';
                userDropdown.style.width = rect.width + 'px';
            }
        });
    }

    // Close dropdown when clicking outside
    document.addEventListener('click', () => {
        if (userDropdown) userDropdown.style.display = 'none';
    });

    // Logout from Dropdown
    if (logoutOption) {
        logoutOption.addEventListener('click', () => {
            localStorage.removeItem('lms_token');
            localStorage.removeItem('lms_user');
            window.location.href = 'login.html';
        });
    }

    // Initialize
    if (!currentChatId && chats.length > 0) {
        currentChatId = chats[0].id;
    }
    renderChats();
    loadCurrentChat();

    window.addEventListener('resize', handleResize);
    handleResize();
});