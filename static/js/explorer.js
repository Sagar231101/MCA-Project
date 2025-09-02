document.addEventListener("DOMContentLoaded", () => {
    const exploreWidget = document.querySelector(".explore-widget");
    const toggleBtn = document.getElementById("explore-toggle-btn");
    const closeBtn = document.querySelector(".close-explore");
    const exploreForm = document.getElementById("explore-form");
    const userInput = document.getElementById("explore-input");
    const resultsContainer = document.getElementById("explore-results");
    const initialMessage = document.querySelector(".explore-body .bot-message");
    const intentButtonsContainer = document.querySelector(".intent-buttons");
    const intentBtns = document.querySelectorAll(".intent-btn");
    const formContainer = document.getElementById("explore-form-container");
    const intentFollowUp = document.getElementById("intent-follow-up");
    const suggestionsContainer = document.getElementById("chatbot-suggestions");
    let currentIntent = '';

    // Event listeners to show/hide the widget
    toggleBtn.addEventListener("click", () => {
        exploreWidget.style.display = exploreWidget.style.display === "flex" ? "none" : "flex";
    });
    closeBtn.addEventListener("click", () => {
        exploreWidget.style.display = "none";
        resetWidget();
    });

    // Handle clicks on the main action buttons
    intentBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            currentIntent = btn.dataset.intent;
            initialMessage.style.display = 'none';
            intentButtonsContainer.style.display = 'none';
            formContainer.style.display = 'block';
            userInput.focus();
            suggestionsContainer.innerHTML = ''; 

            if (currentIntent === 'attractions') {
                intentFollowUp.textContent = "Great! Which city or country would you like to explore?";
                userInput.placeholder = "e.g., Paris";
            } else if (currentIntent === 'budget') {
                intentFollowUp.textContent = "Excellent. What destination should I estimate a budget for?";
                userInput.placeholder = "e.g., Japan";
            } else if (currentIntent === 'transport') {
                intentFollowUp.textContent = "Okay, where are you traveling from and to?";
                userInput.placeholder = "e.g., Mumbai to Delhi";
            } else if (currentIntent === 'chatbot') {
                intentFollowUp.textContent = "Sure, I can help with that. Ask your own question, or select one below.";
                userInput.placeholder = "Type your question here...";
                
                const suggestions = ["How do I cancel a booking?", "What is the refund policy?", "How do custom tours work?"];
                suggestions.forEach(text => {
                    const suggBtn = document.createElement('button');
                    suggBtn.textContent = text;
                    suggBtn.className = 'suggestion-btn';
                    suggBtn.onclick = () => {
                        userInput.value = text;
                        sendMessage();
                    };
                    suggestionsContainer.appendChild(suggBtn);
                });
            }
        });
    });

    // Function to send the message to the backend
    const sendMessage = async () => {
        const userQuery = userInput.value.trim();
        if (userQuery === "") return;

        formContainer.style.display = 'none';
        suggestionsContainer.style.display = 'none';
        resultsContainer.innerHTML = '<div class="bot-message">Thinking...</div>';

        try {
            const response = await fetch('/api/explore', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ place_name: userQuery, intent: currentIntent })
            });
            const data = await response.json();
            
            resultsContainer.innerHTML = ""; // Clear the "Thinking..." message

            if (data.error) {
                appendMessage(data.error, 'bot-message');
            } else if (data.type === 'text') {
                // ✅ NEW: Check if the AI response is empty
                if (data.data && data.data.trim() !== "") {
                    appendMessage(data.data, 'bot-message', true);
                } else {
                    // Show a fallback message if the AI gives an empty response
                    appendMessage("I'm sorry, I couldn't find a specific answer for that. Could you try rephrasing your question?", 'bot-message');
                }
            } else if (data.type === 'attractions' && data.data.length > 0) {
                const list = document.createElement('ul');
                list.className = 'attractions-list';
                data.data.forEach(item => {
                    const listItem = document.createElement('li');
                    listItem.innerHTML = `<strong>${item.name}:</strong> ${item.description}`;
                    list.appendChild(listItem);
                });
                resultsContainer.appendChild(list);
            } else {
                appendMessage("I couldn't find any information for that request. Please try again.", 'bot-message');
            }

        } catch (error) {
            resultsContainer.innerHTML = "";
            appendMessage("There was a network error. Please check your connection and try again.", 'bot-message');
        }
        
        // Add a reset button to start over
        const resetButton = document.createElement('button');
        resetButton.textContent = 'Ask Something Else';
        resetButton.className = 'btn btn-secondary btn-sm mt-3';
        resetButton.onclick = resetWidget;
        resultsContainer.appendChild(resetButton);
    };

    // Helper function to add a message to the chat body
    function appendMessage(text, className, usePreWrap = false) {
        const messageDiv = document.createElement("div");
        messageDiv.className = className;
        messageDiv.textContent = text;
        if (usePreWrap) {
            messageDiv.style.whiteSpace = 'pre-wrap';
        }
        resultsContainer.appendChild(messageDiv);
        return messageDiv;
    }

    // Handle form submission
    exploreForm.addEventListener("submit", (event) => {
        event.preventDefault();
        sendMessage();
    });

    // Function to reset the widget to its initial state
    function resetWidget() {
        resultsContainer.innerHTML = "";
        initialMessage.style.display = 'block';
        intentButtonsContainer.style.display = 'block';
        formContainer.style.display = 'none';
        userInput.value = "";
        currentIntent = '';
        suggestionsContainer.innerHTML = '';
        suggestionsContainer.style.display = 'block';
    }
});
