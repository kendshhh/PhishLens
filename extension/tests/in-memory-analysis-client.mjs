// Development/test fixture only. Production popup wiring uses createAnalysisClient.
export function createInMemoryAnalysisClient(seed = []) {
  const records = new Map(seed.map(record => [record.id, structuredClone(record)]));
  let nextId = 1;
  const copy = value => structuredClone(value);
  return {
    async listAnalyses() { return [...records.values()].map(copy); },
    async getAnalysis(id) {
      if (!records.has(id)) throw Object.assign(new Error("Analysis not found"), { status: 404 });
      return copy(records.get(id));
    },
    async createAnalysis(input) {
      const record = {
        id: `00000000-0000-4000-8000-${String(nextId++).padStart(12, "0")}`,
        subject: input.subject || "", body: input.body, prediction: null, confidence: null,
        risk_level: null, threat_indicators: [], explanation: null,
        created_at: new Date(0).toISOString(), notes: null, feedback: "none",
        analysis_mode: "unknown"
      };
      records.set(record.id, record);
      return copy(record);
    },
    async updateAnalysis(id, patch) {
      if (!records.has(id)) throw Object.assign(new Error("Analysis not found"), { status: 404 });
      const record = { ...records.get(id), ...copy(patch) };
      records.set(id, record);
      return copy(record);
    },
    async deleteAnalysis(id) {
      if (!records.delete(id)) throw Object.assign(new Error("Analysis not found"), { status: 404 });
    }
  };
}
