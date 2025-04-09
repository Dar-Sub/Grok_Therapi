let historyData = [];
let currentSessionIndex = -1;
let currentSessionTitle = null;
let selectedModel = "grok-2";

async function loadHistory() {
    try {
        const response = await fetch("/history");
        historyData = await response.json();
        console.log("Fetched history:", historyData);
        if (!Array.isArray(historyData)) {
            historyData = [];
        }
        displaySessions();
        if (historyData.length > 0) {
            currentSessionIndex = historyData.length - 1;
            currentSessionTitle = historyData[currentSessionIndex].title || "Untitled Session";
            console.log("Loading session on page load:", currentSessionTitle, "at index:", currentSessionIndex);
            loadSession(currentSessionIndex);
        } else {
            console.log("No sessions found, showing create session modal");
            showCreateSessionModal();
        }
    } catch (error) {
        console.error("Error loading history:", error);
        historyData = [];
        displaySessions();
        showCreateSessionModal();
    }
}

function displaySessions() {
    const sessionList = document.getElementById("sessionList");
    if (!sessionList) {
        console.error("Session list element not found");
        return;
    }
    sessionList.innerHTML = "";
    historyData.forEach((session, index) => {
        const sessionItem = document.createElement("div");
        sessionItem.className = `session-item ${index === currentSessionIndex ? "active" : ""}`;
        const title = session.title || "Untitled Session";
        sessionItem.textContent = title.length > 30 ? title.substring(0, 30) + "..." : title;
        sessionItem.onclick = () => loadSession(index);
        sessionList.appendChild(sessionItem);
    });
}

function loadSession(index) {
    currentSessionIndex = index;
    currentSessionTitle = historyData[index].title || "Untitled Session";
    console.log("Loading session:", currentSessionTitle, "at index:", currentSessionIndex);
    let chatBox = document.getElementById("chatBox");
    if (!chatBox) {
        console.error("Chat box element not found in loadSession, creating fallback");
        chatBox = document.createElement("div");
        chatBox.id = "chatBox";
        chatBox.className = "chat-area";
        document.body.appendChild(chatBox);
    }
    chatBox.innerHTML = "";
    const session = historyData[index];
    if (session.messages && Array.isArray(session.messages)) {
        console.log("Messages in session:", session.messages);
        session.messages.forEach(msg => {
            if (msg.user) addMessage("user", msg.user);
            if (msg.grok) addMessage("grok", msg.grok);
        });
    } else {
        console.log("No messages found for session:", currentSessionTitle);
    }
    displaySessions();
}

async function sendMessage() {
    let input = document.getElementById("messageInput");
    if (!input) {
        console.error("Message input element not found, creating fallback");
        input = document.createElement("textarea");
        input.id = "messageInput";
        input.placeholder = "Ask a therapy-related question...";
        document.body.appendChild(input);
    }
    const message = input.value.trim();
    if (!message) return;
    if (!currentSessionTitle) {
        alert("Please create a session first.");
        showCreateSessionModal();
        return;
    }
    addMessage("user", message);
    input.value = "";
    autoResize(input);

    let loadingIndicator = document.getElementById("loadingIndicator");
    if (!loadingIndicator) {
        console.warn("Loading indicator not found, creating a fallback");
        let chatBox = document.getElementById("chatBox");
        if (!chatBox) {
            console.error("Chat box element not found, creating fallback");
            chatBox = document.createElement("div");
            chatBox.id = "chatBox";
            chatBox.className = "chat-area";
            document.body.appendChild(chatBox);
        }
        loadingIndicator = document.createElement("div");
        loadingIndicator.id = "loadingIndicator";
        loadingIndicator.className = "loading-indicator";
        loadingIndicator.style.display = "none";
        loadingIndicator.innerHTML = `
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        `;
        chatBox.appendChild(loadingIndicator);
    }
    loadingIndicator.style.display = "flex";

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message, session_title: currentSessionTitle, model: selectedModel })
        });
        const data = await response.json();
        if (response.ok && data.response) {
            addMessage("grok", data.response);
            await loadHistory();
            currentSessionIndex = historyData.findIndex(session => session.title === currentSessionTitle);
            console.log("Updated currentSessionIndex after sending message:", currentSessionIndex);
            displaySessions();
        } else {
            console.error("Error from server:", data.error || "Unknown error");
            addMessage("grok", "Error: " + (data.error || "Failed to get a response from the server."));
        }
    } catch (error) {
        console.error("Fetch error:", error);
        addMessage("grok", "Error: Failed to connect to the server. Please try again.");
    } finally {
        if (loadingIndicator) {
            loadingIndicator.style.display = "none";
        }
    }
}

function showCreateSessionModal() {
    let modal = document.getElementById("createSessionModal");
    if (!modal) {
        console.error("Create session modal not found, creating fallback");
        modal = document.createElement("div");
        modal.id = "createSessionModal";
        modal.className = "modal";
        modal.innerHTML = `
            <div class="modal-content">
                <h2>Create a session</h2>
                <label for="sessionTitle">Session Title</label>
                <input type="text" id="sessionTitle" placeholder="Define your session with a compelling title...">
                <button onclick="createSession()">Create</button>
            </div>
        `;
        document.body.appendChild(modal);
    }
    modal.style.display = "flex";
    const sessionTitleInput = document.getElementById("sessionTitle");
    if (sessionTitleInput) {
        sessionTitleInput.value = "";
    }
}

async function createSession() {
    const titleInput = document.getElementById("sessionTitle");
    if (!titleInput) {
        console.error("Session title input not found");
        return;
    }
    const title = titleInput.value.trim();
    if (!title) {
        alert("Please enter a session title.");
        return;
    }

    try {
        const response = await fetch("/create_session", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_title: title })
        });
        const data = await response.json();
        if (!response.ok) {
            console.error("Error creating session:", data.error || "Unknown error");
            alert("Error creating session: " + (data.error || "Failed to create session."));
            return;
        }
        console.log("Session created successfully:", title);
    } catch (error) {
        console.error("Fetch error in createSession:", error);
        alert("Error creating session: Failed to connect to the server.");
        return;
    }

    currentSessionTitle = title;
    currentSessionIndex = -1;
    const modal = document.getElementById("createSessionModal");
    if (modal) {
        modal.style.display = "none";
    }
    let chatBox = document.getElementById("chatBox");
    if (chatBox) {
        chatBox.innerHTML = "";
    }
    await loadHistory();
    currentSessionIndex = historyData.findIndex(session => session.title === currentSessionTitle);
    if (currentSessionIndex !== -1) {
        loadSession(currentSessionIndex);
    } else {
        console.error("Newly created session not found in historyData");
    }
}

async function startNewSession() {
    showCreateSessionModal();
}

async function clearHistory() {
    try {
        await fetch("/clear_history", { method: "POST" });
        historyData = [];
        currentSessionIndex = -1;
        currentSessionTitle = null;
        let chatBox = document.getElementById("chatBox");
        if (chatBox) {
            chatBox.innerHTML = "";
        }
        displaySessions();
        showCreateSessionModal();
    } catch (error) {
        console.error("Error clearing history:", error);
        alert("Error clearing history. Please try again.");
    }
}

async function logout() {
    try {
        await fetch("/logout", { method: "POST" });
        window.location.href = "/";
    } catch (error) {
        console.error("Error logging out:", error);
        alert("Error logging out. Please try again.");
    }
}

function addMessage(sender, text) {
    let chatBox = document.getElementById("chatBox");
    if (!chatBox) {
        console.error("Chat box element not found in addMessage, creating fallback");
        chatBox = document.createElement("div");
        chatBox.id = "chatBox";
        chatBox.className = "chat-area";
        document.body.appendChild(chatBox);
    }
    const div = document.createElement("div");
    div.className = `message ${sender}`;

    // Check if the text contains numbered steps (e.g., "1. Step Name\n   Description")
    const lines = text.split("\n");
    let isList = false;
    const ol = document.createElement("ol");
    let currentLi = null;

    lines.forEach(line => {
        line = line.trim();
        if (!line) return; // Skip empty lines

        // Check if the line starts with a number followed by a dot (e.g., "1.")
        const stepMatch = line.match(/^(\d+)\.\s*(.+)$/);
        if (stepMatch) {
            isList = true;
            const stepNumber = stepMatch[1];
            const stepTitle = stepMatch[2].trim();
            currentLi = document.createElement("li");
            const strong = document.createElement("strong");
            strong.textContent = stepTitle;
            currentLi.appendChild(strong);
            ol.appendChild(currentLi);
        } else if (currentLi && line.startsWith("   ")) {
            // This is a description line (indented with spaces)
            const description = line.trim();
            const p = document.createElement("p");
            p.className = "step-description";
            p.textContent = description;
            currentLi.appendChild(p);
        } else {
            // This is a regular paragraph (not part of a list)
            if (isList) {
                div.appendChild(ol);
                isList = false;
            }
            const p = document.createElement("p");
            p.textContent = line;
            div.appendChild(p);
        }
    });

    // Append the last list if it exists
    if (isList) {
        div.appendChild(ol);
    }

    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function autoResize(textarea) {
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${textarea.scrollHeight}px`;
}

function updateModel() {
    const modelSelect = document.getElementById("modelSelect");
    if (modelSelect) {
        selectedModel = modelSelect.value;
        console.log("Selected model updated to:", selectedModel);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const loadingIndicator = document.getElementById("loadingIndicator");
    console.log("Loading indicator on DOMContentLoaded:", loadingIndicator);
    const chatBox = document.getElementById("chatBox");
    console.log("Chat box on DOMContentLoaded:", chatBox);
    const messageInput = document.getElementById("messageInput");
    console.log("Message input on DOMContentLoaded:", messageInput);

    loadHistory();
    if (messageInput) {
        autoResize(messageInput);
    }
});