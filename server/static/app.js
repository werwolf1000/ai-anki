let selectedDeckId = null;
let sessionId = null;
let autoAdvanceTimer = null;
let needsCode = false;

const $ = (id) => document.getElementById(id);

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || res.statusText);
  return data;
}

function showHome() {
  clearTimeout(autoAdvanceTimer);
  sessionId = null;
  $("home-view").classList.remove("hidden");
  $("study-view").classList.add("hidden");
  loadDecks();
}

function showStudy() {
  $("home-view").classList.add("hidden");
  $("study-view").classList.remove("hidden");
}

async function loadConfig() {
  const c = await api("/api/config");
  $("session_limit").value = c.session_limit;
  $("session_limit").max = c.session_limit_max;
  $("pass_score").value = c.pass_score;
  $("max_follow_ups").value = c.max_follow_ups;
  $("auto_advance_sec").value = c.auto_advance_sec;
  $("auto_advance_sec").max = c.auto_advance_max_sec;
  $("ollama_url").value = c.ollama_url;
  $("model").value = c.model;
  $("api_key").value = c.api_key;
  $("timeout").value = c.timeout;
}

async function saveConfig() {
  await api("/api/config", {
    method: "POST",
    body: JSON.stringify({
      session_limit: +$("session_limit").value,
      pass_score: +$("pass_score").value,
      max_follow_ups: +$("max_follow_ups").value,
      auto_advance_sec: +$("auto_advance_sec").value,
      ollama_url: $("ollama_url").value.trim(),
      model: $("model").value.trim(),
      api_key: $("api_key").value.trim(),
      timeout: +$("timeout").value,
    }),
  });
  $("settings-msg").textContent = "Сохранено";
  setTimeout(() => ($("settings-msg").textContent = ""), 2000);
}

async function testOllama() {
  const r = await api("/api/ollama/test", { method: "POST" });
  $("settings-msg").textContent = r.detail;
  $("settings-msg").className = r.ok ? "muted" : "error";
}

async function loadDecks() {
  const { decks } = await api("/api/decks");
  const tbody = $("decks-table").querySelector("tbody");
  tbody.innerHTML = "";
  decks.forEach((d) => {
    const tr = document.createElement("tr");
    if (d.error) {
      tr.innerHTML = `<td>${d.name}</td><td colspan="7" class="error">${d.error}</td>`;
    } else {
      tr.innerHTML = `
        <td>${d.name}</td><td>${d.total}</td><td>${d.mastered}</td><td>${d.passed_today}</td>
        <td>${d.due}</td><td>${d.new}</td><td>${d.weak}</td>
        <td>${d.studied ? d.avg_score : "—"}</td>`;
      tr.onclick = () => {
        tbody.querySelectorAll("tr").forEach((r) => r.classList.remove("selected"));
        tr.classList.add("selected");
        selectedDeckId = d.deck_id;
      };
    }
    tbody.appendChild(tr);
  });
  if (decks.length && !selectedDeckId && !decks[0].error) {
    tbody.rows[0].click();
  }
}

function updateStats(stats) {
  $("study-stats").textContent =
    `Сегодня ${stats.passed_today} · Усвоено ${stats.mastered}/${stats.total} · ` +
    `к повтору ${stats.due} · сессия ${stats.index}/${stats.queue}`;
}

function showCard(card) {
  if (!card) {
    $("question").textContent = "Нет карточек для выбранного режима.";
    $("btn-submit").disabled = true;
    return;
  }
  $("question").textContent = card.question;
  needsCode = card.needs_code;
  $("answer-text").classList.toggle("hidden", needsCode);
  $("answer-code").classList.toggle("hidden", !needsCode);
  $("answer-label").textContent = needsCode
    ? (card.is_live_code ? "Редактор кода — напишите решение" : "Редактор кода — исправьте или дополните")
    : "Ваш ответ (своими словами)";
  if (!needsCode) $("answer-text").value = "";
  $("btn-submit").disabled = false;
  $("btn-next").disabled = true;
  $("feedback").textContent = "";
  $("status").textContent = `лучший ${card.best_score} · попыток ${card.attempts}`;
}

function getAnswer() {
  return needsCode ? $("answer-code").value : $("answer-text").value;
}

function clearAnswer() {
  if (needsCode) $("answer-code").value = "";
  else $("answer-text").value = "";
}

async function startMode(mode) {
  if (!selectedDeckId) {
    alert("Выберите колоду");
    return;
  }
  clearTimeout(autoAdvanceTimer);
  const data = await api("/api/session", {
    method: "POST",
    body: JSON.stringify({ deck_id: selectedDeckId, mode }),
  });
  sessionId = data.session_id;
  $("study-title").textContent = `${data.deck_name} · ${data.mode}`;
  updateStats(data.stats);
  showStudy();
  if (data.empty) showCard(null);
  else showCard(data.card);
}

async function submitAnswer() {
  if (!sessionId) return;
  $("btn-submit").disabled = true;
  $("status").textContent = "Ollama думает…";
  try {
    const r = await api(`/api/session/${sessionId}/answer`, {
      method: "POST",
      body: JSON.stringify({ answer: getAnswer() }),
    });
    $("feedback").textContent = r.feedback;
    updateStats(r.stats);
    $("btn-next").disabled = false;
    $("btn-submit").disabled = !r.can_submit;
    if (r.finalize) clearAnswer();
    if (r.auto_advance_ms > 0) {
      $("status").textContent = `Следующая через ${r.auto_advance_ms / 1000} с…`;
      autoAdvanceTimer = setTimeout(nextCard, r.auto_advance_ms);
    } else if (!r.can_submit) {
      $("status").textContent = "Внесите правки и отправьте снова или нажмите «Следующая →».";
    } else {
      $("status").textContent = "";
    }
  } catch (e) {
    $("feedback").textContent = "❌ " + e.message;
    $("btn-submit").disabled = false;
    $("status").textContent = "";
  }
}

async function nextCard() {
  clearTimeout(autoAdvanceTimer);
  if (!sessionId) return;
  const r = await api(`/api/session/${sessionId}/next`, { method: "POST" });
  if (r.done) {
    alert("Сессия завершена");
    showHome();
    return;
  }
  updateStats(r.stats);
  showCard(r.card);
}

async function showHint() {
  if (!sessionId) return;
  try {
    const r = await api(`/api/session/${sessionId}/hint`, { method: "POST" });
    if (r.hint) $("feedback").textContent += "\n\n💡 " + r.hint;
  } catch (_) { /* ignore */ }
}

$("btn-save").onclick = () => saveConfig().catch((e) => alert(e.message));
$("btn-test").onclick = () => testOllama().catch((e) => alert(e.message));
$("btn-due").onclick = () => startMode("due").catch((e) => alert(e.message));
$("btn-new").onclick = () => startMode("new").catch((e) => alert(e.message));
$("btn-weak").onclick = () => startMode("weak").catch((e) => alert(e.message));
$("btn-all").onclick = () => startMode("all").catch((e) => alert(e.message));
$("btn-back").onclick = showHome;
$("btn-submit").onclick = submitAnswer;
$("btn-next").onclick = nextCard;
$("btn-hint").onclick = showHint;

document.addEventListener("keydown", (e) => {
  if (e.ctrlKey && e.key === "Enter") submitAnswer();
});

loadConfig().catch(console.error);
loadDecks().catch(console.error);
