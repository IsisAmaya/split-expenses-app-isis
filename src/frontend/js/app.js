/**
 * Lógica de la interfaz de usuario.
 * Maneja navegación entre vistas, renderizado y eventos de formularios.
 */

// --- Estado ---
let currentGroupId = null;

// --- Elementos del DOM ---
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);
const groupsView = $("#groups-view");
const detailView = $("#group-detail-view");
const alertEl = $("#alert");

// --- Utilidades ---

function showAlert(message, type = "error") {
    alertEl.textContent = message;
    alertEl.className = `alert alert-${type}`;
    alertEl.hidden = false;
    setTimeout(() => { alertEl.hidden = true; }, 4000);
}

function formatMoney(amount) {
    return `$${Number(amount).toLocaleString("es-CO", { maximumFractionDigits: 0 })}`;
}

function formatDate(dateStr) {
    return new Date(dateStr).toLocaleDateString("es-CO", {
        day: "2-digit", month: "short",
    });
}

const groupEmojis = ["🏖️", "🍕", "🏠", "🎉", "✈️", "🎮", "🍻", "⚽", "🎵", "🚗"];
function getGroupEmoji(name) {
    let hash = 0;
    for (const ch of name) hash = ((hash << 5) - hash + ch.charCodeAt(0)) | 0;
    return groupEmojis[Math.abs(hash) % groupEmojis.length];
}

function getExpenseEmoji(desc) {
    const d = desc.toLowerCase();
    if (d.includes("hotel") || d.includes("aloj")) return "🏨";
    if (d.includes("comida") || d.includes("almuerzo") || d.includes("cena")) return "🍽️";
    if (d.includes("uber") || d.includes("taxi") || d.includes("transport")) return "🚕";
    if (d.includes("cerveza") || d.includes("trago") || d.includes("bar")) return "🍻";
    if (d.includes("super") || d.includes("mercado")) return "🛒";
    return "💳";
}

// --- Navegación ---

function showGroupsView() {
    currentGroupId = null;
    groupsView.hidden = false;
    detailView.hidden = true;
    window.location.hash = "";
    loadGroups();
}

function showDetailView(groupId) {
    currentGroupId = groupId;
    groupsView.hidden = true;
    detailView.hidden = false;
    window.location.hash = `#group/${groupId}`;
    loadGroupDetail(groupId);
}

// --- Renderizado: Lista de grupos ---

async function loadGroups() {
    try {
        const groups = await api.listGroups();
        const list = $("#group-list");
        const empty = $("#no-groups");

        if (groups.length === 0) {
            list.innerHTML = "";
            empty.hidden = false;
            return;
        }

        empty.hidden = true;
        list.innerHTML = groups.map((g) => `
            <a href="#group/${g.id}" class="card group-card" data-id="${g.id}">
                <div class="group-emoji">${getGroupEmoji(g.name)}</div>
                <h3>${g.name}</h3>
                <div class="group-meta">
                    <span>👥 ${g.member_count}</span>
                    <span>📅 ${formatDate(g.created_at)}</span>
                </div>
            </a>
        `).join("");

        list.querySelectorAll(".group-card").forEach((card) => {
            card.addEventListener("click", (e) => {
                e.preventDefault();
                showDetailView(card.dataset.id);
            });
        });
    } catch (err) {
        showAlert(err.message);
    }
}

// --- Renderizado: Detalle de grupo ---

async function loadGroupDetail(groupId) {
    try {
        const [group, expenses, balances, settlements] = await Promise.all([
            api.getGroup(groupId),
            api.listExpenses(groupId),
            api.getBalances(groupId),
            api.getSettlements(groupId),
        ]);

        // Título y miembros
        $("#group-title").textContent = group.name;
        $("#members-bar").innerHTML = group.members
            .map((m) => `<span class="badge">👤 ${m.name}</span>`)
            .join("");

        // Selector de "quién pagó"
        const select = $("#expense-paid-by");
        select.innerHTML = '<option value="">¿Quién pagó?</option>' +
            group.members.map((m) =>
                `<option value="${m.id}">${m.name}</option>`
            ).join("");

        // Stats bar
        const totalGastos = expenses.reduce((sum, e) => sum + Number(e.amount), 0);
        $("#stats-bar").innerHTML = `
            <div class="stat-card">
                <div class="stat-value">${expenses.length}</div>
                <div class="stat-label">Gastos</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${formatMoney(totalGastos)}</div>
                <div class="stat-label">Total</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${group.members.length > 0 ? formatMoney(totalGastos / group.members.length) : "$0"}</div>
                <div class="stat-label">Por persona</div>
            </div>
        `;

        renderExpenses(expenses, groupId);
        renderBalances(balances);
        renderSettlements(settlements);
    } catch (err) {
        showAlert(err.message);
    }
}

function renderExpenses(expenses, groupId) {
    const container = $("#expenses-table");
    const empty = $("#no-expenses");

    if (expenses.length === 0) {
        container.innerHTML = "";
        empty.hidden = false;
        return;
    }

    empty.hidden = true;
    container.innerHTML = `<div class="expense-list">
        ${expenses.map((e) => `
            <div class="expense-item">
                <div class="expense-icon">${getExpenseEmoji(e.description)}</div>
                <div class="expense-info">
                    <div class="expense-desc">${e.description}</div>
                    <div class="expense-meta">
                        <span>Pagó <strong>${e.paid_by}</strong></span>
                        <span>·</span>
                        <span>${formatDate(e.created_at)}</span>
                        <span>·</span>
                        ${e.splits.map((s) =>
                            `<span class="badge badge-sm">${s.member_name}</span>`
                        ).join("")}
                    </div>
                </div>
                <div class="expense-amount">${formatMoney(e.amount)}</div>
                <button class="btn-delete" data-id="${e.id}" title="Eliminar">🗑️</button>
            </div>
        `).join("")}
    </div>`;

    container.querySelectorAll(".btn-delete").forEach((btn) => {
        btn.addEventListener("click", async () => {
            try {
                await api.deleteExpense(groupId, btn.dataset.id);
                loadGroupDetail(groupId);
            } catch (err) {
                showAlert(err.message);
            }
        });
    });
}

function renderBalances(balances) {
    const container = $("#balances-list");
    const empty = $("#no-balances");

    if (balances.length === 0) {
        container.innerHTML = "";
        empty.hidden = false;
        return;
    }

    empty.hidden = true;
    container.innerHTML = balances.map((b) => {
        const val = Number(b.balance);
        const cls = val > 0 ? "positive" : val < 0 ? "negative" : "zero";
        let text;
        if (val > 0) text = `+${formatMoney(val)}`;
        else if (val < 0) text = `-${formatMoney(Math.abs(val))}`;
        else text = "✓ En paz";

        const icon = val > 0 ? "🟢" : val < 0 ? "🔴" : "⚪";

        return `
            <div class="card balance-card ${cls}">
                <span class="balance-name">${icon} ${b.member}</span>
                <span class="balance-amount">${text}</span>
            </div>
        `;
    }).join("");
}

function renderSettlements(settlements) {
    const container = $("#settlements-list");
    const empty = $("#no-settlements");

    if (settlements.length === 0) {
        container.innerHTML = "";
        empty.hidden = false;
        return;
    }

    empty.hidden = true;
    container.innerHTML = settlements.map((s) => `
        <div class="card settlement-card">
            <span class="settlement-from">🔴 ${s.from_member}</span>
            <span class="settlement-arrow">→</span>
            <span class="settlement-to">🟢 ${s.to_member}</span>
            <span class="settlement-amount">${formatMoney(s.amount)}</span>
        </div>
    `).join("");
}

// --- Event listeners ---

// Toggle create group form
$("#toggle-create-form").addEventListener("click", () => {
    const wrapper = $("#create-group-form-wrapper");
    const btn = $("#toggle-create-form");
    wrapper.hidden = !wrapper.hidden;
    btn.hidden = !btn.hidden;
});

$("#close-create-form").addEventListener("click", () => {
    $("#create-group-form-wrapper").hidden = true;
    $("#toggle-create-form").hidden = false;
});

// --- Members tag input ---
let membersList = [];

function renderMemberTags() {
    const container = $("#members-tags");
    container.innerHTML = membersList.map((name, i) => `
        <span class="member-tag">
            ${name}
            <button type="button" class="member-tag-remove" data-index="${i}">✕</button>
        </span>
    `).join("");

    container.querySelectorAll(".member-tag-remove").forEach((btn) => {
        btn.addEventListener("click", () => {
            membersList.splice(parseInt(btn.dataset.index), 1);
            renderMemberTags();
        });
    });
}

function addMember() {
    const input = $("#group-members");
    const name = input.value.trim();
    if (!name) return;
    if (membersList.includes(name)) {
        showAlert(`"${name}" ya está en el grupo`);
        return;
    }
    membersList.push(name);
    input.value = "";
    input.focus();
    renderMemberTags();
}

$("#add-member-btn").addEventListener("click", addMember);

$("#group-members").addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        e.preventDefault();
        addMember();
    }
});

// Create group
$("#create-group-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = $("#group-name").value.trim();

    if (membersList.length < 2) {
        showAlert("El grupo debe tener al menos 2 miembros");
        return;
    }

    try {
        const group = await api.createGroup(name, membersList);
        $("#group-name").value = "";
        membersList = [];
        renderMemberTags();
        $("#create-group-form-wrapper").hidden = true;
        $("#toggle-create-form").hidden = false;
        showAlert("¡Grupo creado!", "success");
        showDetailView(group.id);
    } catch (err) {
        showAlert(err.message);
    }
});

// Add expense
$("#add-expense-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = {
        description: $("#expense-desc").value.trim(),
        amount: parseFloat($("#expense-amount").value),
        paid_by_id: $("#expense-paid-by").value,
    };

    try {
        await api.createExpense(currentGroupId, data);
        $("#expense-desc").value = "";
        $("#expense-amount").value = "";
        $("#expense-paid-by").value = "";
        loadGroupDetail(currentGroupId);
    } catch (err) {
        showAlert(err.message);
    }
});

// Back link
$("#back-link").addEventListener("click", (e) => {
    e.preventDefault();
    showGroupsView();
});

// Tabs
$$(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
        $$(".tab").forEach((t) => t.classList.remove("active"));
        $$(".tab-content").forEach((c) => c.classList.remove("active"));
        tab.classList.add("active");
        $(`#tab-${tab.dataset.tab}`).classList.add("active");
    });
});

// --- Routing por hash ---

function handleRoute() {
    const hash = window.location.hash;
    const match = hash.match(/^#group\/(.+)$/);
    if (match) {
        showDetailView(match[1]);
    } else {
        showGroupsView();
    }
}

window.addEventListener("hashchange", handleRoute);

// --- Init ---
handleRoute();
