/* ============================================================
   main.js — YouTube Recommender Web App
   Includes: theme toggle, AJAX search, render cards
   ============================================================ */
'use strict';

// ── State ─────────────────────────────────────────────────────────────────────
const state = { mode: 'video', category: 'Semua' };

// ── DOM Refs ───────────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);

const modeToggle      = $('mode-toggle');
const categorySelect  = $('category-select');
const queryInput      = $('query-input');
const topkSlider      = $('topk-slider');
const topkDisplay     = $('topk-display');
const searchBtn       = $('search-btn');
const btnIcon         = $('btn-icon');
const btnSpinner      = $('btn-spinner');
const btnLabel        = $('btn-label');
const validationMsg   = $('validation-msg');
const resultsSection  = $('results-section');
const resultsContainer= $('results-container');
const resultsMeta     = $('results-meta');
const resultsBadge    = $('results-badge');
const themeToggle     = $('theme-toggle');
const iconMoon        = $('icon-moon');
const iconSun         = $('icon-sun');


// ══════════════════════════════════════════════════════════════════
// THEME TOGGLE (Dark ↔ Light)
// ══════════════════════════════════════════════════════════════════
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('yt-recommender-theme', theme);
  if (theme === 'dark') {
    iconMoon.style.display = 'block';
    iconSun.style.display  = 'none';
  } else {
    iconMoon.style.display = 'none';
    iconSun.style.display  = 'block';
  }
}

function initTheme() {
  const saved = localStorage.getItem('yt-recommender-theme') || 'dark';
  applyTheme(saved);
  themeToggle.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme');
    applyTheme(current === 'dark' ? 'light' : 'dark');
  });
}


// ══════════════════════════════════════════════════════════════════
// CATEGORIES
// ══════════════════════════════════════════════════════════════════
async function loadCategories() {
  try {
    const res  = await fetch('/api/categories');
    const data = await res.json();
    (data.categories || []).forEach(cat => {
      const opt = document.createElement('option');
      opt.value = cat;
      opt.textContent = cat;
      categorySelect.appendChild(opt);
    });
  } catch { /* ignore – fallback to "Semua" */ }

  categorySelect.addEventListener('change', () => {
    state.category = categorySelect.value;
  });
}


// ══════════════════════════════════════════════════════════════════
// MODE TOGGLE
// ══════════════════════════════════════════════════════════════════
function initModeToggle() {
  modeToggle.querySelectorAll('.mode-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      modeToggle.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.mode = btn.dataset.mode;
    });
  });
}


// ══════════════════════════════════════════════════════════════════
// SLIDER
// ══════════════════════════════════════════════════════════════════
function initSlider() {
  const updateTrack = () => {
    const pct = ((topkSlider.value - topkSlider.min) / (topkSlider.max - topkSlider.min)) * 100;
    topkSlider.style.setProperty('--pct', pct + '%');
    topkDisplay.textContent = topkSlider.value;
  };
  updateTrack();
  topkSlider.addEventListener('input', updateTrack);
}


// ══════════════════════════════════════════════════════════════════
// SEARCH
// ══════════════════════════════════════════════════════════════════
function validate() {
  const errs = [];
  if (!queryInput.value.trim()) errs.push('Masukkan kata kunci pencarian.');
  return errs;
}

function showValidation(errs) {
  if (!errs.length) { validationMsg.style.display = 'none'; return; }
  validationMsg.textContent = errs.join(' ');
  validationMsg.style.display = 'block';
}

function setLoading(on) {
  searchBtn.disabled      = on;
  btnIcon.style.display   = on ? 'none'  : 'block';
  btnSpinner.style.display= on ? 'block' : 'none';
  btnLabel.textContent    = on ? 'Memproses...' : 'Cari Rekomendasi';
}

function clearResults() {
  resultsContainer.innerHTML   = '';
  resultsSection.style.display = 'none';
  validationMsg.style.display  = 'none';
}

async function handleSearch() {
  const errs = validate();
  showValidation(errs);
  if (errs.length) return;

  setLoading(true);
  clearResults();

  try {
    const res  = await fetch('/api/recommend', {
      method : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify({
        query   : queryInput.value.trim(),
        mode    : state.mode,
        category: categorySelect.value,
        top_k   : parseInt(topkSlider.value),
      }),
    });
    const data = await res.json();
    if (!res.ok || data.error) { showValidation([data.error || 'Server error.']); return; }
    renderResults(data);
  } catch {
    showValidation(['Gagal terhubung ke server. Pastikan Flask sudah berjalan.']);
  } finally {
    setLoading(false);
  }
}


// ══════════════════════════════════════════════════════════════════
// RENDER RESULTS
// ══════════════════════════════════════════════════════════════════
function renderResults(data) {
  const { results, query_original, query_processed, mode, category } = data;

  const catLabel = (category && !['Semua','Semua Kategori'].includes(category))
    ? ` · Kategori: <strong>${esc(category)}</strong>` : '';
  resultsMeta.innerHTML =
    `Query: <strong>"${esc(query_original)}"</strong>${catLabel}<br/>` +
    `Processed: <em>${esc(query_processed)}</em> · <strong>${results.length}</strong> hasil`;

  resultsBadge.textContent = mode === 'video' ? '🎬 Judul Video' : '📺 Channel';
  resultsBadge.className   = `results-badge ${mode === 'video' ? 'badge-video' : 'badge-channel'}`;

  resultsSection.style.display = 'block';
  resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

  if (!results.length) {
    resultsContainer.innerHTML = `
      <div class="empty-state">
        <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
        </svg>
        <h3>Tidak ada hasil ditemukan</h3>
        <p>Coba kata kunci lain atau ubah filter kategori.</p>
      </div>`;
    return;
  }

  const frag = document.createDocumentFragment();
  results.forEach((item, idx) => {
    const el = mode === 'video' ? buildVideoCard(item) : buildChannelCard(item, idx);
    el.style.animationDelay = `${idx * 55}ms`;
    frag.appendChild(el);
  });
  resultsContainer.appendChild(frag);
}


// ── Video Card ─────────────────────────────────────────────────────────────────
function buildVideoCard(item) {
  const el  = document.createElement('div');
  el.className = 'result-card';
  const { barCls, badgeCls } = tier(item.similarity_score);

  el.innerHTML = `
    <div class="rank-badge ${rankCls(item.rank)}">#${item.rank}</div>
    <div class="card-body">
      <div class="card-title">
        <a href="${esc(item.link)}" target="_blank" rel="noopener">${esc(item.judul)}</a>
      </div>
      <div class="card-meta">
        <span class="meta-item">
          <svg viewBox="0 0 20 20" fill="currentColor" width="13"><path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"/></svg>
          <a href="${esc(item.link_channel)}" target="_blank" rel="noopener">${esc(item.nama_channel)}</a>
        </span>
        <span class="meta-item">
          <svg viewBox="0 0 20 20" fill="currentColor" width="13"><path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/><path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/></svg>
          ${esc(item.jumlah_tayangan)} tayangan
        </span>
        <span class="meta-item">
          <svg viewBox="0 0 20 20" fill="currentColor" width="13"><path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd"/></svg>
          ${esc(item.tanggal_upload)}
        </span>
        <span class="category-tag ${catCls(item.kategori)}">${esc(item.kategori)}</span>
      </div>
      <div class="sim-bar-wrap">
        <span class="sim-label">Similarity</span>
        <div class="sim-bar-bg">
          <div class="sim-bar-fill ${barCls}" style="width:${Math.round(item.similarity_score*100)}%"></div>
        </div>
        <span class="sim-score-badge ${badgeCls}">${item.similarity_score.toFixed(4)}</span>
      </div>
    </div>`;
  return el;
}


// ── Channel Card ───────────────────────────────────────────────────────────────
function buildChannelCard(item, idx) {
  const el = document.createElement('div');
  el.className = 'channel-card';
  const { barCls, badgeCls } = tier(item.similarity_score);
  const letter = (item.nama_channel || '?').replace('@','')[0].toUpperCase();

  // Top videos HTML
  let vidsHtml = '';
  if (item.top_videos && item.top_videos.length) {
    const rows = item.top_videos.map((v, vi) => `
      <div class="vid-item">
        <span class="vid-idx">${vi+1}.</span>
        <span class="vid-title-text"><a href="${esc(v.link)}" target="_blank" rel="noopener">${esc(v.judul)}</a></span>
        <span class="vid-sim">${v.similarity_judul.toFixed(4)}</span>
      </div>`).join('');
    vidsHtml = `
      <div class="top-vids-section">
        <div class="top-vids-title">🎬 Video Paling Mirip dari Channel Ini</div>
        ${rows}
      </div>`;
  }

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
        </div>
        <div class="sim-bar-wrap" style="margin-top:10px;">
          <span class="sim-label">Similarity</span>
          <div class="sim-bar-bg">
            <div class="sim-bar-fill ${barCls}" style="width:${Math.round(item.similarity_score*100)}%"></div>
          </div>
          <span class="sim-score-badge ${badgeCls}">${item.similarity_score.toFixed(4)}</span>
        </div>
      </div>
    </div>
    ${vidsHtml}`;
  return el;
}


// ── Helpers ────────────────────────────────────────────────────────────────────
function tier(s) {
  if (s >= 0.85) return { barCls:'sim-high-bar', badgeCls:'sim-high' };
  if (s >= 0.75) return { barCls:'sim-mid-bar',  badgeCls:'sim-mid'  };
  return               { barCls:'sim-low-bar',  badgeCls:'sim-low'  };
}

function rankCls(r) {
  return r === 1 ? 'rank-1' : r === 2 ? 'rank-2' : r === 3 ? 'rank-3' : 'rank-n';
}

function catCls(cat) {
  const map = {
    Gadgets:'cat-gadgets', Gaming:'cat-gaming', Food:'cat-food',
    News:'cat-news', Music:'cat-music', Sports:'cat-sports',
    Automotive:'cat-automotive', Education:'cat-education',
    Entertainment:'cat-entertainment', Animals:'cat-animals',
  };
  return map[cat] || 'cat-default';
}

function esc(s) {
  return String(s||'')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}


// ══════════════════════════════════════════════════════════════════
// INIT
// ══════════════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  loadCategories();
  initModeToggle();
  initSlider();
  searchBtn.addEventListener('click', handleSearch);
  queryInput.addEventListener('keydown', e => { if (e.key === 'Enter') handleSearch(); });
});
