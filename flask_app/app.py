"""Flask web application for channel-only recommendations."""

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


@app.route('/api/channels')
def api_channels():
    """Return list channel yang tersedia untuk dipilih di web."""
    channels = recommender.get_channels()
    return jsonify({'channels': channels})


@app.route('/api/recommend', methods=['POST'])
def api_recommend():
    """
    Endpoint rekomendasi utama.
    Body JSON: { channel_name, top_k }
    """
    data = request.get_json(force=True)

    channel_name = (data.get('channel_name') or '').strip()
    top_k = data.get('top_k', 5)

    # ── Validasi ──────────────────────────────────────────────────
    errors = []
    if not channel_name:
        errors.append('Channel input tidak boleh kosong.')
    if errors:
        return jsonify({'error': ' '.join(errors)}), 400

    try:
        top_k = max(1, min(20, int(top_k)))
    except (TypeError, ValueError):
        top_k = 5

    # ── Jalankan Rekomendasi ───────────────────────────────────────
    try:
        result = recommender.recommend_channel(
            channel_name=channel_name,
            top_k=top_k,
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
