
import { getAnalyses } from "./api.js";

export async function loadHistory(baseUrl) {
    const container = document.getElementById("history-list");

    if (!container) {
        console.error("History container not found");
        return;
    }

    container.textContent = "Loading history...";

    try {
        const analyses = await getAnalyses(baseUrl);
        container.replaceChildren();

        if (analyses.length === 0) {
            container.textContent = "No saved analyses yet.";
            return;
        }

        for (const analysis of analyses) {
            const card = document.createElement("div");
            card.className = "history-item";

            const title = document.createElement("h3");
            title.textContent = analysis.subject || "No subject";

            const result = document.createElement("p");
            result.textContent = "Prediction: " +
                (analysis.prediction || "Pending");

            const risk = document.createElement("p");
            risk.textContent = "Risk: " +
                (analysis.risk_level || "Unknown");

            const confidence = document.createElement("p");
            confidence.textContent = "Confidence: " +
                (analysis.confidence == null
                    ? "N/A"
                    : Math.round(analysis.confidence * 100) + "%");

            const explanation = document.createElement("p");
            explanation.textContent = analysis.explanation || "";

            card.append(title, result, risk, confidence, explanation);
            container.appendChild(card);
        }

    } catch (error) {
        console.error("History error:", error);
        container.textContent = "Failed to load history. Please try again.";
    }
}
