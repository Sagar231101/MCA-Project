document.addEventListener("DOMContentLoaded", () => {
    const exploreWidget = document.querySelector(".explore-widget");
    const toggleBtn = document.getElementById("explore-toggle-btn");
    const closeBtn = document.querySelector(".close-explore");
    const exploreForm = document.getElementById("explore-form");
    const userInput = document.getElementById("explore-input");
    const resultsContainer = document.getElementById("explore-results");

    // Toggle widget visibility
    toggleBtn.addEventListener("click", () => {
        exploreWidget.style.display = exploreWidget.style.display === "flex" ? "none" : "flex";
    });
    closeBtn.addEventListener("click", () => {
        exploreWidget.style.display = "none";
    });

    // Handle form submission
    exploreForm.addEventListener("submit", async (event) => {
        event.preventDefault(); // Prevent page reload
        const placeName = userInput.value.trim();
        if (placeName === "") return;

        resultsContainer.innerHTML = '<div class="bot-message">Thinking...</div>';
        userInput.value = "";

        try {
            const response = await fetch('/api/explore', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ place_name: placeName })
            });

            const data = await response.json();
            resultsContainer.innerHTML = ""; // Clear "Thinking..." message

            if (data.error) {
                resultsContainer.innerHTML = `<div class="bot-message">${data.error}</div>`;
            } else if (data.attractions && data.attractions.length > 0) {
                data.attractions.forEach(attraction => {
                    const item = document.createElement('div');
                    item.className = 'attraction-item';
                    item.innerHTML = `<h6>${attraction.name}</h6><p>${attraction.description}</p>`;
                    resultsContainer.appendChild(item);
                });
            } else {
                resultsContainer.innerHTML = '<div class="bot-message">Sorry, I couldn\'t find any attractions for that place.</div>';
            }
        } catch (error) {
            console.error("Error:", error);
            resultsContainer.innerHTML = '<div class="bot-message">There was a network error. Please try again.</div>';
        }
    });
});
