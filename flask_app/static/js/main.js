/* ============================================================
  main.js — YouTube Channel Recommender Web App
  ============================================================ */
"use strict";

// ── State ─────────────────────────────────────────────────────────────────────
const state = {
  channel: "",
  channelCategoryMap: {},
};

// ── DOM Refs ───────────────────────────────────────────────────────────────────
const $ = (id) => document.getElementById(id);

const channelSelect = $("channel-input");
const selectedCategoryMeta = $("selected-category-meta");
const topkSlider = $("topk-slider");
const topkDisplay = $("topk-display");
const searchBtn = $("search-btn");
const btnIcon = $("btn-icon");
const btnSpinner = $("btn-spinner");
const btnLabel = $("btn-label");
const validationMsg = $("validation-msg");
const resultsSection = $("results-section");
const resultsContainer = $("results-container");
const resultsMeta = $("results-meta");
const resultsBadge = $("results-badge");
const themeToggle = $("theme-toggle");
const iconMoon = $("icon-moon");
const iconSun = $("icon-sun");

// ══════════════════════════════════════════════════════════════════
// THEME TOGGLE (Dark ↔ Light)
// ══════════════════════════════════════════════════════════════════
function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("yt-recommender-theme", theme);
  if (theme === "dark") {
    iconMoon.style.display = "block";
    iconSun.style.display = "none";
  } else {
    iconMoon.style.display = "none";
    iconSun.style.display = "block";
  }
}

function initTheme() {
  const saved = localStorage.getItem("yt-recommender-theme") || "dark";
  applyTheme(saved);
  themeToggle.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme");
    applyTheme(current === "dark" ? "light" : "dark");
  });
}

// ══════════════════════════════════════════════════════════════════
// CHANNELS
// ══════════════════════════════════════════════════════════════════
async function loadChannels() {
  try {
    const res = await fetch("/api/channels");
    const data = await res.json();
    (data.channels || []).forEach((item) => {
      const ch = typeof item === "string" ? item : item.nama_channel;
      const kategori = typeof item === "string" ? "-" : item.kategori || "-";

      state.channelCategoryMap[ch] = kategori;

      const opt = document.createElement("option");
      opt.value = ch;
      opt.textContent =
        kategori && kategori !== "-" ? `${ch} — ${kategori}` : ch;
      channelSelect.appendChild(opt);
    });
  } catch {
    /* ignore – fallback to default option */
  }

  channelSelect.addEventListener("change", () => {
    state.channel = channelSelect.value;
    updateSelectedCategoryMeta();
  });

  updateSelectedCategoryMeta();
}

function updateSelectedCategoryMeta() {
  const ch = channelSelect.value.trim();
  if (!ch) {
    selectedCategoryMeta.textContent =
      "Pilih channel untuk melihat kategorinya.";
    selectedCategoryMeta.className = "selected-category-meta";
    return;
  }

  const kategori = state.channelCategoryMap[ch] || "-";
  selectedCategoryMeta.innerHTML = `Kategori channel input: <strong>${esc(kategori)}</strong>`;
  selectedCategoryMeta.className = "selected-category-meta is-selected";
}

// ══════════════════════════════════════════════════════════════════
// SLIDER
// ══════════════════════════════════════════════════════════════════
function initSlider() {
  const updateTrack = () => {
    const pct =
      ((topkSlider.value - topkSlider.min) /
        (topkSlider.max - topkSlider.min)) *
      100;
    topkSlider.style.setProperty("--pct", pct + "%");
    topkDisplay.textContent = topkSlider.value;
  };
  updateTrack();
  topkSlider.addEventListener("input", updateTrack);
}

// ══════════════════════════════════════════════════════════════════
// SEARCH
// ══════════════════════════════════════════════════════════════════
function validate() {
  const errs = [];
  if (!channelSelect.value.trim()) errs.push("Pilih channel acuan.");
  return errs;
}

function showValidation(errs) {
  if (!errs.length) {
    validationMsg.style.display = "none";
    return;
  }
  validationMsg.textContent = errs.join(" ");
  validationMsg.style.display = "block";
}

function setLoading(on) {
  searchBtn.disabled = on;
  btnIcon.style.display = on ? "none" : "block";
  btnSpinner.style.display = on ? "block" : "none";
  btnLabel.textContent = on ? "Memproses..." : "Cari Channel Mirip";
}

function clearResults() {
  resultsContainer.innerHTML = "";
  resultsSection.style.display = "none";
  validationMsg.style.display = "none";
}

async function handleSearch() {
  const errs = validate();
  showValidation(errs);
  if (errs.length) return;

  setLoading(true);
  clearResults();

  try {
    const res = await fetch("/api/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        channel_name: channelSelect.value.trim(),
        top_k: parseInt(topkSlider.value),
      }),
    });
    const data = await res.json();
    if (!res.ok || data.error) {
      showValidation([data.error || "Server error."]);
      return;
    }
    renderResults(data);
  } catch {
    showValidation([
      "Gagal terhubung ke server. Pastikan Flask sudah berjalan.",
    ]);
  } finally {
    setLoading(false);
  }
}

// ══════════════════════════════════════════════════════════════════
// RENDER RESULTS
// ══════════════════════════════════════════════════════════════════
function renderResults(data) {
  const { results, channel_input, input_category, same_category_count } = data;

  const sameCount =
    typeof same_category_count === "number" ? same_category_count : 0;
  const diffCount = Math.max(0, results.length - sameCount);

  resultsMeta.innerHTML =
    `Channel acuan: <strong>${esc(channel_input)}</strong><br/>` +
    `Kategori input: <strong>${esc(input_category || "-")}</strong> · ` +
    `Menampilkan <strong>${results.length}</strong> channel paling mirip ` +
    `(Sama kategori: <strong>${sameCount}</strong>, Beda kategori: <strong>${diffCount}</strong>)`;

  resultsBadge.textContent = "📺 Rekomendasi Channel";
  resultsBadge.className = "results-badge badge-channel";

  resultsSection.style.display = "block";
  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });

  if (!results.length) {
    resultsContainer.innerHTML = `
      <div class="empty-state">
        <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
        </svg>
        <h3>Tidak ada hasil ditemukan</h3>
        <p>Coba pilih channel lain atau ubah jumlah rekomendasi.</p>
      </div>`;
    return;
  }

  const frag = document.createDocumentFragment();
  results.forEach((item, idx) => {
    const el = buildChannelCard(item, idx);
    el.style.animationDelay = `${idx * 55}ms`;
    frag.appendChild(el);
  });
  resultsContainer.appendChild(frag);
}

// ── Channel Card ───────────────────────────────────────────────────────────────
function buildChannelCard(item, idx) {
  const el = document.createElement("div");
  el.className = "channel-card";
  const { barCls, badgeCls } = tier(item.similarity_score);
  const letter = (item.nama_channel || "?").replace("@", "")[0].toUpperCase();

  el.innerHTML = `
    <div class="channel-card-header">
      <div class="ch-avatar av-${idx % 8}">${letter}</div>
      <div style="flex:1;min-width:0;">
        <div class="ch-name">
          <a href="${esc(item.link_channel)}" target="_blank" rel="noopener">${esc(item.nama_channel)}</a>
          <span style="font-size:0.72rem;color:var(--text-muted);margin-left:7px;">#${item.rank}</span>
        </div>
        <div class="ch-info">
          <span class="meta-item">
            <svg viewBox="0 0 20 20" fill="currentColor" width="13"><path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm0 2a7 7 0 00-7 7h14a7 7 0 00-7-7z" clip-rule="evenodd"/></svg>
            ${esc(item.jumlah_pelanggan)} pelanggan
          </span>
          <span class="category-tag ${catCls(item.kategori)}">${esc(item.kategori)}</span>
          <span class="match-tag ${item.is_same_category ? "match-same" : "match-diff"}">
            ${item.is_same_category ? "Sama kategori" : "Beda kategori"}
          </span>
        </div>
        <div class="sim-bar-wrap" style="margin-top:10px;">
          <span class="sim-label">Similarity</span>
          <div class="sim-bar-bg">
            <div class="sim-bar-fill ${barCls}" style="width:${Math.round(item.similarity_score * 100)}%"></div>
          </div>
          <span class="sim-score-badge ${badgeCls}">${item.similarity_score.toFixed(4)}</span>
        </div>
      </div>
    </div>`;
  return el;
}

// ── Helpers ────────────────────────────────────────────────────────────────────
function tier(s) {
  if (s >= 0.85) return { barCls: "sim-high-bar", badgeCls: "sim-high" };
  if (s >= 0.75) return { barCls: "sim-mid-bar", badgeCls: "sim-mid" };
  return { barCls: "sim-low-bar", badgeCls: "sim-low" };
}

function rankCls(r) {
  return r === 1
    ? "rank-1"
    : r === 2
      ? "rank-2"
      : r === 3
        ? "rank-3"
        : "rank-n";
}

function catCls(cat) {
  const map = {
    Gadgets: "cat-gadgets",
    Gaming: "cat-gaming",
    Food: "cat-food",
    News: "cat-news",
    Music: "cat-music",
    Sports: "cat-sports",
    Automotive: "cat-automotive",
    Education: "cat-education",
    Entertainment: "cat-entertainment",
    Animals: "cat-animals",
  };
  return map[cat] || "cat-default";
}

function esc(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// ══════════════════════════════════════════════════════════════════
// INIT
// ══════════════════════════════════════════════════════════════════
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  loadChannels();
  initSlider();
  searchBtn.addEventListener("click", handleSearch);
  channelSelect.addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleSearch();
  });
});
