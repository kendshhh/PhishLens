// extension/js/popup.js

document.addEventListener("DOMContentLoaded", () => {
  const loading = document.getElementById("loading");
  const error = document.getElementById("error");
  const empty = document.getElementById("empty");
  const list = document.getElementById("history-list");

  // Simulate a 1-second loading state, then show mock data (Synthetic Fixture)
  setTimeout(() => {
    loading.classList.add("hidden");

    // Mock data to satisfy Issue #6
    const mockData = [
      { subject: "URGENT: Password Reset", risk_level: "High" },
      { subject: "Weekly Newsletter", risk_level: "Low" }
    ];

    if (mockData.length === 0) {
      empty.classList.remove("hidden");
    } else {
      mockData.forEach(item => {
        const li = document.createElement("li");
        li.textContent = `Subject: ${item.subject} | Risk: ${item.risk_level}`;
        list.appendChild(li);
      });
    }
  }, 1000); 
});