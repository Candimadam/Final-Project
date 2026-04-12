"""Backend sistem rekomendasi channel YouTube."""

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR       = Path(__file__).parent
OUTPUT_DIR     = BASE_DIR.parent / 'output'
SIMILARITY_MATRIX_PATH = OUTPUT_DIR / 'similarity_matrix.csv'
CHANNEL_METADATA_PATH  = OUTPUT_DIR / 'video_metadata.csv'

# ─── Global State (diisi saat initialize()) ───────────────────────────────────
_similarity_df = None
_channel_names = None   # list of str
_channel_info  = None   # dict channel_name → {kategori, jumlah_pelanggan, link_channel}


# ═════════════════════════════════════════════════════════════════════════════
# INITIALIZATION
# ═════════════════════════════════════════════════════════════════════════════

def initialize():
    """
    Load semua resource (similarity matrix, metadata) ke memory.
    Dipanggil SEKALI saat startup Flask.
    """
    global _similarity_df, _channel_names, _channel_info

    print(f"\n{'='*55}")
    print("  INISIALISASI RECOMMENDER")
    print(f"{'='*55}")

    # ── 1. Similarity matrix ──────────────────────────────────────
    print("[1/2] Memuat similarity matrix...")
    if not SIMILARITY_MATRIX_PATH.exists():
        raise FileNotFoundError(
            f"File '{SIMILARITY_MATRIX_PATH.name}' tidak ditemukan di '{OUTPUT_DIR}'."
        )

    _similarity_df = pd.read_csv(SIMILARITY_MATRIX_PATH, index_col=0)
    _channel_names = _similarity_df.index.tolist()
    print(f"      ✓ Similarity matrix: {_similarity_df.shape}")

    # ── 2. Metadata ───────────────────────────────────────────────
    print("[2/2] Memuat metadata channel...")
    if not CHANNEL_METADATA_PATH.exists():
        raise FileNotFoundError(
            f"File '{CHANNEL_METADATA_PATH.name}' tidak ditemukan di '{OUTPUT_DIR}'."
        )

    meta_df = pd.read_csv(CHANNEL_METADATA_PATH)
    ch_unique = meta_df.drop_duplicates(subset='nama_channel').set_index('nama_channel')

    _channel_info = {}
    for ch in _channel_names:
        if ch in ch_unique.index:
            row = ch_unique.loc[ch]
            _channel_info[ch] = {
                'kategori'         : str(row['kategori']),
                'jumlah_pelanggan' : int(row['jumlah_pelanggan']),
                'link_channel'     : str(row['link_channel']),
            }
        else:
            _channel_info[ch] = {'kategori': '-', 'jumlah_pelanggan': 0, 'link_channel': '#'}

    print(f"\n{'='*55}")
    print("  ✅ Recommender siap digunakan!")
    print(f"{'='*55}\n")

# ═════════════════════════════════════════════════════════════════════════════
# RECOMMENDATION FUNCTIONS
# ═════════════════════════════════════════════════════════════════════════════

def get_channels():
    """Return list channel + kategori untuk dropdown frontend."""
    if not _channel_names:
        return []

    return [
        {
            'nama_channel': ch,
            'kategori': _channel_info.get(ch, {}).get('kategori', '-'),
        }
        for ch in _channel_names
    ]


def recommend_channel(channel_name, top_k=5):
    """
    Fungsi rekomendasi channel berdasarkan channel input.

    Parameters
    ----------
    channel_name : str  – nama channel input
    top_k        : int  – jumlah hasil yang dikembalikan

    Returns
    -------
    dict – { results, channel_input, mode }
    """
    if not channel_name or not channel_name.strip():
        return {'error': 'Channel tidak boleh kosong'}

    if _similarity_df is None or _channel_info is None:
        return {'error': 'Sistem belum diinisialisasi'}

    source_channel = channel_name.strip()
    source_category = _channel_info.get(source_channel, {}).get('kategori', '-')

    results = _recommend_channels(source_channel, top_k)
    same_count = sum(1 for r in results if r.get('is_same_category'))

    return {
        'results': results,
        'channel_input': source_channel,
        'input_category': source_category,
        'same_category_count': same_count,
        'mode': 'channel',
    }


def _recommend_channels(channel_name, top_k):
    """Rekomendasi Top-K channel berdasarkan similarity matrix."""
    global _similarity_df, _channel_info

    if channel_name not in _similarity_df.index:
        raise ValueError(
            f"Channel '{channel_name}' tidak ditemukan."
        )

    sims = _similarity_df.loc[channel_name].drop(labels=channel_name)
    top_matches = sims.sort_values(ascending=False).head(top_k)
    source_category = _channel_info.get(channel_name, {}).get('kategori', '-')

    results = []
    for rank, (ch, score) in enumerate(top_matches.items(), start=1):
        info = _channel_info.get(ch, {})
        target_category = info.get('kategori', '-')
        is_same_category = target_category == source_category

        results.append({
            'rank': rank,
            'nama_channel': ch,
            'kategori': target_category,
            'jumlah_pelanggan': _fmt_number(info.get('jumlah_pelanggan', 0)),
            'link_channel': info.get('link_channel', '#'),
            'similarity_score': round(float(score), 4),
            'is_same_category': is_same_category,
        })
    return results


def _fmt_number(n):
    """Format angka besar menjadi string ringkas (1.2 Jt, 13.8 Rb, dll.)."""
    try:
        n = int(n)
    except (TypeError, ValueError):
        return str(n)
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f} Jt"
    elif n >= 1_000:
        return f"{n/1_000:.1f} Rb"
    return str(n)
