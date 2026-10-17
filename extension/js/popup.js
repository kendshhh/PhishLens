import { API_BASE_URL } from "./config.js";

document.addEventListener("DOMContentLoaded", async () => {
  const loading = document.getElementById("loading");
  const error = document.getElementById("error");
  const empty = document.getElementById("empty");
  const list = document.getElementById("history-list");

  try {
    // Connect to the public API URL defined in config.js
    const res = await fetch(`${API_BASE_URL}/api/analyses`);
    
    if (!res.ok) {
      throw new Error(`Server returned HTTP ${res.status}`);
    }
    
    const data = await res.json();
    
    // Hide the loading state once the response is received
    loading.classList.add("hidden");

    // Handle the empty state if there are no records in the database
    if (!Array.isArray(data) || data.length === 0) {
      empty.classList.remove("hidden");
      return;
    }

    // STRICT REQUIREMENT: Render content safely as text to prevent XSS
    data.forEach(item => {
      const li = document.createElement("li");
      const subject = item.subject || "Analyzed Email";
      const risk = item.risk_level || "Unknown";
      
      li.textContent = `Subject: ${subject} | Risk: ${risk}`;
      list.appendChild(li);
    });

  } catch (err) {
    // Handle failures gracefully without breaking the console
    loading.classList.add("hidden");
    error.textContent = `Connection failed: ${err.message}`;
    error.classList.remove("hidden");
  }
});