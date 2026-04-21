/**
 * Capa de comunicación con la API REST del backend.
 * Todas las llamadas HTTP al backend pasan por aquí.
 */
const API_BASE = globalThis.API_BASE_URL || "/api";

globalThis.api = {
    async request(method, path, body = null) {
        const options = {
            method,
            headers: { "Content-Type": "application/json" },
        };
        if (body) {
            options.body = JSON.stringify(body);
        }

        const response = await fetch(`${API_BASE}${path}`, options);

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `Error ${response.status}`);
        }

        if (response.status === 204) return null;
        return response.json();
    },

    // --- Grupos ---
    createGroup(name, members) {
        return this.request("POST", "/groups/", { name, members });
    },

    listGroups() {
        return this.request("GET", "/groups/");
    },

    getGroup(groupId) {
        return this.request("GET", `/groups/${groupId}`);
    },

    deleteGroup(groupId) {
        return this.request("DELETE", `/groups/${groupId}`);
    },

    // --- Gastos ---
    createExpense(groupId, data) {
        return this.request("POST", `/groups/${groupId}/expenses`, data);
    },

    listExpenses(groupId) {
        return this.request("GET", `/groups/${groupId}/expenses`);
    },

    deleteExpense(groupId, expenseId) {
        return this.request("DELETE", `/groups/${groupId}/expenses/${expenseId}`);
    },

    // --- Balances ---
    getBalances(groupId) {
        return this.request("GET", `/groups/${groupId}/balances`);
    },

    getSettlements(groupId) {
        return this.request("GET", `/groups/${groupId}/settlements`);
    },

    // --- Health ---
    async healthCheck() {
        const response = await fetch("/health");
        return response.json();
    },
};
