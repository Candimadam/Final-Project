"""
app.py – Flask Web Application
Sistem Rekomendasi Channel YouTube menggunakan IndoBERT
"""

from flask import Flask, render_template, request, jsonify
import recommender

app = Flask(__name__)


# ─── Startup ─────────────────────────────────────────────────────────────────
@app.before_request
def startup():
    """Load semua resource SEKALI sebelum request pertama."""
    global _initialized
    if not _initialized:
        recommender.initialize()
        _initialized = True


_initialized = False


# ─── Routes ──────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/categories')
def api_categories():
    """Return list kategori dari dataset."""
    cats = recommender.get_categories()
    return jsonify({'categories': cats})


@app.route('/api/recommend', methods=['POST'])
def api_recommend():
    """
    Endpoint rekomendasi utama.
    Body JSON: { query, mode, category, top_k }
    """
    data = request.get_json(force=True)

    query    = (data.get('query') or '').strip()
    mode     = (data.get('mode') or 'video').strip()
    category = (data.get('category') or 'Semua').strip()
    top_k    = data.get('top_k', 5)

    # ── Validasi ──────────────────────────────────────────────────
    errors = []
    if not query:
        errors.append('Query pencarian tidak boleh kosong.')
    if mode not in ('video', 'channel'):
        errors.append('Jenis rekomendasi tidak valid.')
    if errors:
        return jsonify({'error': ' '.join(errors)}), 400

    try:
        top_k = max(1, min(20, int(top_k)))
    except (TypeError, ValueError):
        top_k = 5

    # ── Jalankan Rekomendasi ───────────────────────────────────────
    try:
        result = recommender.recommend(
            query    = query,
            mode     = mode,
            category = category,
            top_k    = top_k,
        )
        return jsonify(result)
    except Exception as exc:
        return jsonify({'error': f'Server error: {str(exc)}'}), 500


# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    # Inisialisasi langsung saat run manual (bukan via before_request)
    recommender.initialize()
    _initialized = True
    app.run(debug=False, host='0.0.0.0', port=5000)
