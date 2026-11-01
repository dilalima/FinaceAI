const state = { registerMode: false, evolutionChart: null, categoryChart: null };
const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const $ = (id) => document.getElementById(id);

function setMessage(id, message = "") { $(id).textContent = message; }
function show(view) { $("auth-view").classList.toggle("hidden", view !== "auth"); $("dashboard-view").classList.toggle("hidden", view !== "dashboard"); }

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const token = localStorage.getItem("financeai_token");
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(path, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "Não foi possível concluir a operação.");
  return data;
}

function renderCharts(data) {
  if (state.evolutionChart) state.evolutionChart.destroy();
  if (state.categoryChart) state.categoryChart.destroy();
  const labels = data.monthly_evolution.map((item) => new Date(`${item.month}T12:00:00`).toLocaleDateString("pt-BR", { month: "short" }));
  state.evolutionChart = new Chart($("evolution-chart"), { type: "line", data: { labels, datasets: [
    { label: "Receitas", data: data.monthly_evolution.map((i) => i.income), borderColor: "#2367e8", backgroundColor: "rgba(35,103,232,.1)", fill: true, tension: .35 },
    { label: "Despesas", data: data.monthly_evolution.map((i) => i.expenses), borderColor: "#d95362", backgroundColor: "transparent", tension: .35 },
  ] }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "bottom", labels: { usePointStyle: true, boxWidth: 7 } } }, scales: { y: { beginAtZero: true, ticks: { callback: (value) => money.format(value) } }, x: { grid: { display: false } } } } });
  const colors = ["#2367e8", "#5e9bff", "#8bb8ff", "#1b9a6c", "#f4b740", "#d95362"];
  state.categoryChart = new Chart($("category-chart"), { type: "doughnut", data: { labels: data.expenses_by_category.map((i) => i.category), datasets: [{ data: data.expenses_by_category.map((i) => i.total), backgroundColor: colors, borderWidth: 0 }] }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, cutout: "70%" } });
}

function renderDashboard(data, user) {
  $("total-balance").textContent = money.format(data.total_balance); $("monthly-income").textContent = money.format(data.monthly_income); $("monthly-expenses").textContent = money.format(data.monthly_expenses); $("monthly-savings").textContent = money.format(data.monthly_savings); $("pending-count").textContent = data.pending_transactions; $("user-name").textContent = user.full_name;
  $("account-count").textContent = `${data.accounts.length} ${data.accounts.length === 1 ? "conta" : "contas"}`;
  $("accounts-list").innerHTML = data.accounts.length ? data.accounts.map((a) => `<div class="account-item"><span class="account-name"><span class="dot"></span>${a.account_name}</span><strong>${money.format(a.balance)}</strong></div>`).join("") : "<p class=\"form-message\">Nenhuma conta cadastrada.</p>";
  $("category-list").innerHTML = data.expenses_by_category.length ? data.expenses_by_category.slice(0, 5).map((c) => `<div class="category-item"><span class="category-name"><span class="dot"></span>${c.category}</span><strong>${money.format(c.total)}</strong></div>`).join("") : "<p class=\"form-message\">Nenhuma despesa registrada neste mês.</p>";
  if (data.top_expense_category) { $("insight-title").textContent = `${data.top_expense_category} concentra seus gastos.`; $("insight-text").textContent = `A categoria representa ${money.format(data.top_expense_category_total)} nas despesas pagas deste mês.`; }
  renderCharts(data);
}

async function loadDashboard() { setMessage("dashboard-message"); try { const user = await api("/auth/me"); const data = await api("/dashboard/summary"); renderDashboard(data, user); } catch (error) { setMessage("dashboard-message", error.message); if (error.message.includes("token")) { localStorage.removeItem("financeai_token"); show("auth"); } } }

async function loadTransactions() { const transactions = await api("/finance/transactions"); const rows = transactions.slice(0, 8).map((item) => `<tr><td>${item.description}</td><td>${item.category}</td><td>${new Date(`${item.transaction_date}T12:00:00`).toLocaleDateString("pt-BR")}</td><td class="${item.type === "income" ? "income-value" : "expense-value"}">${item.type === "income" ? "+" : "−"} ${money.format(item.amount)}</td></tr>`).join(""); $("transactions-list").innerHTML = rows ? `<table class="transactions-table"><thead><tr><th>Descrição</th><th>Categoria</th><th>Data</th><th>Valor</th></tr></thead><tbody>${rows}</tbody></table>` : "<p class=\"form-message\">Nenhuma movimentação registrada.</p>"; }
async function loadDashboardData() { await loadDashboard(); if (!$("dashboard-view").classList.contains("hidden")) { try { await loadTransactions(); } catch (error) { setMessage("dashboard-message", error.message); } } }

$("auth-toggle").addEventListener("click", () => { state.registerMode = !state.registerMode; $("name-field").classList.toggle("hidden", !state.registerMode); $("auth-title").textContent = state.registerMode ? "Criar sua conta" : "Entrar na sua conta"; $("auth-subtitle").textContent = state.registerMode ? "Comece a organizar sua vida financeira." : "Use seus dados para acessar seu painel financeiro."; $("auth-submit").textContent = state.registerMode ? "Criar conta" : "Entrar"; $("auth-toggle").textContent = state.registerMode ? "Já tenho uma conta" : "Ainda não tenho uma conta"; });
$("auth-form").addEventListener("submit", async (event) => { event.preventDefault(); setMessage("auth-message"); const payload = { email: $("email").value, password: $("password").value }; if (state.registerMode) payload.full_name = $("full-name").value; try { if (state.registerMode) await api("/auth/register", { method: "POST", body: JSON.stringify(payload) }); const login = await api("/auth/login", { method: "POST", body: JSON.stringify({ email: payload.email, password: payload.password }) }); localStorage.setItem("financeai_token", login.access_token); show("dashboard"); await loadDashboardData(); } catch (error) { setMessage("auth-message", error.message); } });
$("logout-button").addEventListener("click", () => { localStorage.removeItem("financeai_token"); show("auth"); }); $("refresh-button").addEventListener("click", loadDashboardData);
const modal = $("modal"); const accountFields = $("account-fields"); const transactionFields = $("transaction-fields");
function openModal(type) { modal.classList.remove("hidden"); const transactionMode = type === "transaction"; $("modal-title").textContent = transactionMode ? "Novo lançamento" : "Nova conta"; accountFields.classList.toggle("hidden", transactionMode); transactionFields.classList.toggle("hidden", !transactionMode); $("finance-form").dataset.type = type; setMessage("modal-message"); if (transactionMode) { api("/finance/accounts").then((accounts) => { $("transaction-account").innerHTML = accounts.map((a) => `<option value="${a.id}">${a.name}</option>`).join(""); }).catch((error) => setMessage("modal-message", error.message)); } }
function closeModal() { modal.classList.add("hidden"); $("finance-form").reset(); }
$("new-account-button").addEventListener("click", () => openModal("account")); $("new-transaction-button").addEventListener("click", () => openModal("transaction")); $("close-modal").addEventListener("click", closeModal); modal.addEventListener("click", (event) => { if (event.target === modal) closeModal(); });
$("finance-form").addEventListener("submit", async (event) => { event.preventDefault(); const transactionMode = event.currentTarget.dataset.type === "transaction"; const payload = transactionMode ? { account_id: Number($("transaction-account").value), description: $("transaction-description").value, amount: $("transaction-amount").value, type: $("transaction-type").value, category: $("transaction-category").value, transaction_date: $("transaction-date").value, status: $("transaction-status").value } : { name: $("account-name").value, institution: $("account-institution").value || null, account_type: $("account-type").value, initial_balance: $("initial-balance").value }; try { await api(transactionMode ? "/finance/transactions" : "/finance/accounts", { method: "POST", body: JSON.stringify(payload) }); closeModal(); await loadDashboardData(); } catch (error) { setMessage("modal-message", error.message); } });
$("assistant-form").addEventListener("submit", async (event) => { event.preventDefault(); const question = $("assistant-question").value.trim(); if (!question) return; setMessage("assistant-message", "Consultando seus dados..."); $("assistant-answer").textContent = ""; try { const result = await api("/assistant/chat", { method: "POST", body: JSON.stringify({ question }) }); $("assistant-answer").textContent = result.answer; setMessage("assistant-message"); } catch (error) { $("assistant-answer").textContent = "Não foi possível gerar uma resposta agora."; setMessage("assistant-message", error.message); } });
if (localStorage.getItem("financeai_token")) { show("dashboard"); loadDashboardData(); } else show("auth");
