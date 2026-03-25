document.addEventListener("DOMContentLoaded", () => {
    const API_BASE = "http://localhost:5000";

let currentUser = null;

const signupForm = document.getElementById("signup-form");
const loginForm = document.getElementById("login-form");
const chatContainer = document.getElementById("chat-container");
const chatHistoryDiv = document.getElementById("chat-history");
const userInfo = document.getElementById("user-info");
const faqSearchBox = document.getElementById("faq-search-box");
const faqSearchResults = document.getElementById("faq-search-results");
const feedbackBox = document.getElementById("feedback-review");
const loadFeedbackBtn = document.getElementById("load-feedback-btn");
const modal = document.getElementById("image-modal");
const modalClose = document.getElementById("modal-close");

if(modalClose){
    modalClose.onclick = () => {
        modal.style.display = "none";
    };
}

if(modal){
    modal.onclick = (e) => {
        if(e.target === modal){
            modal.style.display = "none";
        }
    };
}

let feedbackVisible = false;

if (loadFeedbackBtn) {

    loadFeedbackBtn.onclick = async () => {

        // hide if already visible
        if (feedbackVisible) {
            feedbackBox.innerHTML = "";
            loadFeedbackBtn.textContent = "Show Bad Responses";
            feedbackVisible = false;
            return;
        }

        const res = await fetch(
            `${API_BASE}/admin/bad_feedback?email=${currentUser.email}`
        );

        const data = await res.json();

        feedbackBox.innerHTML = "";

        data.items.forEach(row => {

            const div = document.createElement("div");

            div.style.borderBottom = "1px solid #444";
            div.style.padding = "8px";
            div.style.marginBottom = "10px";

            div.innerHTML = `
                <b>Question:</b> ${row.ques}<br>
                <b>Bot Answer:</b> ${row.ans}<br>

                <textarea class="faq-answer-box"
                placeholder="Write improved answer here"
                style="
                    width:100%;
                    margin-top:6px;
                    background:#1e1e1e;
                    border:1px solid #444;
                    color:white;
                    padding:6px;
                    border-radius:4px;
                "></textarea>

                <button class="faq-add-btn"
                style="margin-top:6px">
                    Add to FAQ
                </button>
            `;

            const btn = div.querySelector(".faq-add-btn");

            btn.onclick = () => convertToFaq(row.ques, div);

            feedbackBox.appendChild(div);
        });

        loadFeedbackBtn.textContent = "Hide Bad Responses";
        feedbackVisible = true;
    };
}
window.convertToFaq = async function(question, container){

    const textarea = container.querySelector(".faq-answer-box");
    const answer = textarea.value.trim();

    if(!answer){
        showStatus("Please write improved answer first", "#d9534f");
        return;
    }

    const newFaq = [{
        id: "faq_" + Date.now(),
        question: question,
        answer: answer
    }];

    const res = await fetch(`${API_BASE}/admin/upload_faqs`, {
        method:"POST",
        headers:{
            "Content-Type":"application/json"
        },
        body:JSON.stringify({
            admin_email: currentUser.email,
            faqs: newFaq
        })
    });

    const data = await res.json();

    if(res.ok){
        showStatus("FAQ added successfully!");
        container.remove();
    }
    else{
        showStatus(data.error || "Failed to add FAQ", "#d9534f");
    }
}
/* ===========================
      UI SWITCHING
=========================== */
document.getElementById("goto-login").onclick = (e) => {
    e.preventDefault();
    signupForm.style.display = "none";
    loginForm.style.display = "block";
};

document.getElementById("goto-signup").onclick = (e) => {
    e.preventDefault();
    signupForm.style.display = "block";
    loginForm.style.display = "none";
};
// to enable back button
const backButton = document.getElementById("back-button");
const adminPanel = document.getElementById("admin-panel");
const faqJsonInput = document.getElementById("faq-json-input");
const uploadFaqBtn = document.getElementById("upload-faq-btn");



/* ===========================
        SIGNUP
=========================== */
document.getElementById("signup-btn").onclick = async () => {
    console.log("SIGNUP BUTTON CLICKED");

    const name = document.getElementById("signup-name").value.trim();
    const email = document.getElementById("signup-email").value.trim();
    const password = document.getElementById("signup-password").value.trim();

    if (!name || !email || !password) {
        showStatus("All fields are required.", "#d9534f");  // red error
        return;
    }

    const res = await fetch(`${API_BASE}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password }),
    });

    const data = await res.json();

    if (res.ok) {
        // SUCCESS
        showStatus("Signup successful! Please log in.");
        signupForm.style.display = "none";
        loginForm.style.display = "block";
    } else {
        // ERROR
        showStatus(data.message, "#d9534f");
    }
};


/* ===========================
        LOGIN
=========================== */
document.getElementById("login-btn").onclick = async () => {
    const email = document.getElementById("login-email").value.trim();
    const password = document.getElementById("login-password").value.trim();

    const res = await fetch(`${API_BASE}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
    });

    const data = await res.json();

    if (!res.ok) {
        showStatus(data.message, "#d9534f"); // ❌ wrong login – show red
        return;
    }

    // -----------------
    // ✔ LOGIN SUCCESS! 
    // -----------------
    currentUser = data;

    userInfo.style.display = "block";
    document.getElementById("username-display").textContent =
        `Logged in as: ${data.name || data.email}`;

    loginForm.style.display = "none";
    chatContainer.style.display = "block";

    chatHistoryDiv.innerHTML = ""; // clear chat screen
    
    if (data.role === "admin") {
        adminPanel.style.display = "block";
    } else {
        adminPanel.style.display = "none";
    }
    
    showStatus("Logged in successfully!");   
};


/* ===========================
        LOGOUT
=========================== */
document.getElementById("logout-btn").onclick = async () => {
    await fetch(`${API_BASE}/logout`, { method: "POST" });

    currentUser = null;

    // hide chat
    chatContainer.style.display = "none";
    
    adminPanel.style.display = "none";


    // show login again
    loginForm.style.display = "block";

    // hide user info
    userInfo.style.display = "none";

    // clear chat screen
    chatHistoryDiv.innerHTML = "";

    // also show the default chatbot description again
    document.getElementById("chat-description").style.display = "block";

    showStatus("Logged out.");
};

/* ===========================
        SEND MESSAGE
=========================== */
document.getElementById("send-btn").onclick = sendMessage;

async function sendMessage() {
    const input = document.getElementById("message-input");
    const text = input.value.trim();
    if (!text) return;

    render(text, "user");
    input.value = "";
    showTyping();

    const body = { question: text };
    if (currentUser) body.email = currentUser.email;

    const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });

    

    const data = await res.json();
    removeTyping();
    if (res.ok) {
        render(data.answer, "bot", data.chat_id, data.image);
    } else {
        render(data.error, "bot");
    }
}

/* ===========================
      CHAT RENDERING
=========================== */
function render(msg, role, chatId=null, image=null) {

    const div = document.createElement("div");
    div.className = `message ${role}-message`;

    const text = document.createElement("div");
    text.innerText = msg;
    div.appendChild(text);

    if(image){

    const img = document.createElement("img");

    img.src = `/static/${image}`;
    img.style.width = "100%";
    img.style.maxWidth = "250px";
    img.style.marginTop = "8px";
    img.style.borderRadius = "6px";
    img.style.cursor = "zoom-in";

    img.onclick = () => {
        const modal = document.getElementById("image-modal");
        const modalImg = document.getElementById("modal-img");

        modal.style.display = "flex";
        modalImg.src = img.src;
    };

    div.appendChild(img);
}

    chatHistoryDiv.appendChild(div);

    if (role === "bot" && chatId) {

        const feedback = document.createElement("div");
        feedback.style.marginTop = "5px";

        feedback.innerHTML = `
            <span style="cursor:pointer">👍</span>
            <span style="cursor:pointer;margin-left:10px">👎</span>
        `;

        const up = feedback.children[0];
        const down = feedback.children[1];

        up.onclick = () => {
            sendFeedback(chatId,1);
            feedback.remove();
        };

        down.onclick = () => {
            sendFeedback(chatId,0);
            feedback.remove();
        };

        div.appendChild(feedback);
    }

    chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
}
function showTyping() {
    const div = document.createElement("div");
    div.className = "message bot-message typing";
    div.id = "typing-indicator";

    div.innerHTML = `
        <span></span>
        <span></span>
        <span></span>
    `;

    chatHistoryDiv.appendChild(div);
    chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
}

function removeTyping() {
    const typing = document.getElementById("typing-indicator");
    if (typing) typing.remove();
}



/* ===========================
      LOAD HISTORY
=========================== */
async function loadHistory() {
    if (!currentUser) return;

    const res = await fetch(`${API_BASE}/history?email=${currentUser.email}`);
    const data = await res.json();

    chatHistoryDiv.innerHTML = "";

    (data.chats || []).forEach((c) => {
        render(c.question, "user");
        render(c.answer, "bot", c.chat_id);
    });
}
// history button
document.getElementById("history-button").onclick = () => {
    if (!currentUser) {
        showStatus("Please log in first.", true);
        return;
    }

    chatHistoryDiv.innerHTML = "";
    loadHistory();

    document.getElementById("chat-description").style.display = "none";

    document.getElementById("chat-input-area").style.display = "none";
    document.getElementById("suggestion-area").style.display = "none";

    backButton.style.display = "block";
};

backButton.onclick = () => {
    chatHistoryDiv.innerHTML = "";

    backButton.style.display = "none";

    document.getElementById("chat-description").style.display = "block";
    document.getElementById("chat-input-area").style.display = "flex";
    document.getElementById("suggestion-area").style.display = "block";
};

//to show status if login or signup is successful or not
function showStatus(msg, color="#28a745") {
    const bar = document.getElementById("status-bar");
    bar.textContent = msg;
    bar.style.background = color;
    bar.style.display = "block";

    setTimeout(() => bar.style.display = "none", 2500);
}



/* ===========================
    SUGGESTION BUTTONS
=========================== */
document.querySelectorAll(".suggestion").forEach((btn) => {
    btn.onclick = () => {
        document.getElementById("message-input").value = btn.textContent;
        sendMessage();
    };
});

if (uploadFaqBtn) {
    uploadFaqBtn.onclick = async () => {
    if (!currentUser || currentUser.role !== "admin") {
        showStatus("Only admin can upload FAQs.", "#d9534f");
        return;
    }

    const fileInput = document.getElementById("faq-file-input");
    const file = fileInput.files[0];

    if (!file) {
        showStatus("Please select a JSON file.", "#d9534f");
        return;
    }

    // Read the file content
    let text;
    try {
        text = await file.text();
    } catch (e) {
        showStatus("Failed to read file.", "#d9534f");
        return;
    }

    let parsed;
    try {
        parsed = JSON.parse(text);
    } catch (e) {
        showStatus("Invalid JSON format.", "#d9534f");
        return;
    }

    const res = await fetch(`${API_BASE}/admin/upload_faqs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            admin_email: currentUser.email,
            faqs: parsed
        }),
    });

    const data = await res.json();

    if (res.ok) {
        showStatus(`FAQs uploaded: ${data.count}`);
    } else {
        showStatus(data.error || "Upload failed", "#d9534f");
    }
    };
}

/* ===========================
      ADMIN FAQ SEARCH
=========================== */

// Cache FAQs after first load
let cachedFaqs = [];

// Load FAQs from backend
async function loadFaqs() {
    const res = await fetch(`${API_BASE}/admin/get_faqs`);
    const data = await res.json();
    cachedFaqs = data.faqs || [];
}

// Attach search only if elements exist
if (faqSearchBox && faqSearchResults) {

    faqSearchBox.addEventListener("input", async () => {
        const text = faqSearchBox.value.trim().toLowerCase();

        // Load FAQs only once
        if (cachedFaqs.length === 0) {
            await loadFaqs();
        }

        // Clear box
        faqSearchResults.innerHTML = "";

        // Hide box on empty input
        if (text.length === 0) {
            faqSearchResults.style.display = "none";
            return;
        }

        // Filter results
        const found = cachedFaqs.filter(f =>
            f.question.toLowerCase().includes(text) ||
            f.answer.toLowerCase().includes(text)
        );

        // No matches
        if (found.length === 0) {
            faqSearchResults.style.display = "block";
            faqSearchResults.innerHTML =
                `<p style="padding:6px; color:#888;">No matches found.</p>`;
            return;
        }

        // Show results
        faqSearchResults.style.display = "block";
        faqSearchResults.innerHTML = found.map(f => `
            <div style="
                padding:8px;
                border-bottom:1px solid #444;
                margin-bottom:6px;
            ">
                <b>${f.question}</b><br>
                <span style="color:#aaa;">${f.answer}</span>
            </div>
        `).join("");
    });
}
async function sendFeedback(chatId,value){

    await fetch(`${API_BASE}/feedback`,{
        method:"POST",
        headers:{
            "Content-Type":"application/json"
        },
        body:JSON.stringify({
            chat_id:chatId,
            feedback:value
        })
    });

    showStatus("Feedback saved!");
}
});
// autofill faq upload form
function fillFaq(question){

    const faqBox = document.getElementById("faq-search-box");

    faqBox.value = question;

    showStatus("Admin can now add improved FAQ");
}
