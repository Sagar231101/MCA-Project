// Replace the content of your static/js/explorer.js file with this

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
    let currentIntent = '';

    // Toggle widget visibility
    toggleBtn.addEventListener("click", () => {
        exploreWidget.style.display = exploreWidget.style.display === "flex" ? "none" : "flex";
    });
    closeBtn.addEventListener("click", () => {
        exploreWidget.style.display = "none";
        resetWidget();
    });

 // Handle intent button clicks
    intentBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            currentIntent = btn.dataset.intent;
            initialMessage.style.display = 'none';
            intentButtonsContainer.style.display = 'none';
            formContainer.style.display = 'block';
            userInput.focus();

            if (currentIntent === 'attractions') {
                intentFollowUp.textContent = "Great! Which city or country would you like to explore?";
                userInput.placeholder = "e.g., Paris";
            } else if (currentIntent === 'budget') {
                intentFollowUp.textContent = "Excellent. What destination should I estimate a budget for?";
                userInput.placeholder = "e.g., Japan";
            } else if (currentIntent === 'transport') {
                intentFollowUp.textContent = "Okay, where are you traveling from and to?";
                userInput.placeholder = "e.g., Mumbai to Delhi";
            } 
            // ✅ NEW: Handle the chatbot intent
            else if (currentIntent === 'chatbot') {
                intentFollowUp.textContent = "Sure, How Can I help you?";
                userInput.placeholder = "e.g., How do I cancel my booking?";
            }
        });
    });

    // Handle form submission
    exploreForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const placeName = userInput.value.trim();
        if (placeName === "") return;

        formContainer.style.display = 'none';
        resultsContainer.innerHTML = '<div class="bot-message">Thinking...</div>';

        try {
            const response = await fetch('/api/explore', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ place_name: placeName, intent: currentIntent })
            });

            const data = await response.json();
            resultsContainer.innerHTML = "";

            if (data.error) {
                resultsContainer.innerHTML = `<div class="bot-message">${data.error}</div>`;
            } else if (data.type === 'attractions' && data.data.length > 0) {
                data.data.forEach(attraction => {
                    const item = document.createElement('div');
                    item.className = 'attraction-item';
                    item.innerHTML = `<h6>${attraction.name}</h6><p>${attraction.description}</p>`;
                    resultsContainer.appendChild(item);
                });
            } else if (data.type === 'text') {
                const item = document.createElement('div');
                item.className = 'bot-message';
                item.style.whiteSpace = 'pre-wrap';
                item.textContent = data.data;
                resultsContainer.appendChild(item);
            } else {
                resultsContainer.innerHTML = '<div class="bot-message">Sorry, I couldn\'t find any information.</div>';
            }
        } catch (error) {
            resultsContainer.innerHTML = '<div class="bot-message">There was a network error. Please try again.</div>';
        }
        
        // Add a reset button
        const resetButton = document.createElement('button');
        resetButton.textContent = 'Ask Something Else';
        resetButton.className = 'btn btn-secondary btn-sm mt-3';
        resetButton.onclick = resetWidget;
        resultsContainer.appendChild(resetButton);
    });

    function resetWidget() {
        resultsContainer.innerHTML = "";
        initialMessage.style.display = 'block';
        intentButtonsContainer.style.display = 'block';
        formContainer.style.display = 'none';
        userInput.value = "";
        currentIntent = '';
    }
});
