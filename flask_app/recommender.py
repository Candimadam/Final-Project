"""
recommender.py
Backend sistem rekomendasi YouTube Channel menggunakan IndoBERT.
Diload sekali saat startup Flask, kemudian setiap request hanya
melakukan embedding query + cosine similarity.
"""

import os, re, json, numpy as np, pandas as pd
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
import stanza

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR       = Path(__file__).parent
OUTPUT_DIR     = BASE_DIR.parent / 'output'
DATA_JSON_PATH = BASE_DIR.parent / 'data_video.json'

INDOBERT_MODEL = 'indolem/indobert-base-uncased'
DEVICE         = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# ─── Stopwords (sama persis dengan notebook Bagian 5b) ────────────────────────
INDONESIAN_STOPWORDS = {
    'yang', 'ini', 'itu', 'dan', 'atau', 'di', 'ke', 'dari', 'pada', 'untuk',
    'dengan', 'adalah', 'ada', 'akan', 'sudah', 'telah', 'bisa', 'bukan',
    'tidak', 'tak', 'belum', 'jangan', 'agar', 'supaya', 'karena', 'sebab',
    'jika', 'bila', 'kalau', 'maka', 'ketika', 'saat', 'setelah', 'sebelum',
    'sehingga', 'walaupun', 'meskipun', 'bahwa', 'namun', 'tetapi', 'tapi',
    'saya', 'aku', 'kamu', 'anda', 'dia', 'mereka', 'kita', 'kami',
    'juga', 'lagi', 'masih', 'pun', 'pula', 'hanya', 'saja', 'lebih',
    'sangat', 'sekali', 'begitu', 'seperti', 'antara', 'oleh', 'bagi', 'tentang',
    'dalam', 'luar', 'atas', 'bawah', 'sejak', 'hingga', 'sampai', 'selama',
    'kemudian', 'lalu', 'jadi', 'menjadi', 'merupakan', 'yaitu', 'yakni',
    'si', 'sang', 'para', 'tiap', 'setiap', 'semua', 'seluruh', 'beberapa',
    'paling', 'makin', 'semakin', 'cukup', 'agak', 'hampir',
    'serta', 'maupun', 'baik', 'buat', 'tanpa', 'kecuali', 'bahkan',
    'apa', 'siapa', 'dimana', 'kemana', 'darimana', 'kapan', 'berapa',
    'mengapa', 'kenapa', 'bagaimana', 'gimana',
    'lg', 'gak', 'ga', 'udah', 'udh', 'nih', 'dong', 'deh', 'sih',
    'yuk', 'yup', 'ya', 'iya', 'oke', 'ok', 'gitu', 'gini', 'tuh',
}

# ─── Global State (diisi saat initialize()) ───────────────────────────────────
_tokenizer        = None
_model            = None
_nlp_stanza       = None
_video_embeddings = None   # np.ndarray (n_videos, 768)
_video_metadata   = None   # pd.DataFrame
_channel_matrix   = None   # np.ndarray (n_channels, 768), L2-normalized
_channel_names    = None   # list of str
_channel_info     = None   # dict channel_name → {kategori, jumlah_pelanggan, link_channel}
_categories       = None   # list of str


# ═════════════════════════════════════════════════════════════════════════════
# INITIALIZATION
# ═════════════════════════════════════════════════════════════════════════════

def initialize():
    """
    Load semua resource (model, embedding, metadata) ke memory.
    Dipanggil SEKALI saat startup Flask.
    """
    global _tokenizer, _model, _nlp_stanza
    global _video_embeddings, _video_metadata
    global _channel_matrix, _channel_names, _channel_info, _categories

    print(f"\n{'='*55}")
    print(f"  INISIALISASI RECOMMENDER")
    print(f"  Device: {DEVICE}")
    print(f"{'='*55}")

    # ── 1. IndoBERT ───────────────────────────────────────────────
    print("[1/5] Memuat IndoBERT tokenizer & model...")
    _tokenizer = AutoTokenizer.from_pretrained(INDOBERT_MODEL)
    _model     = AutoModel.from_pretrained(INDOBERT_MODEL)
    _model     = _model.to(DEVICE)
    _model.eval()
    print(f"      ✓ IndoBERT siap → {DEVICE}")

    # ── 2. Stanza ─────────────────────────────────────────────────
    print("[2/5] Memuat Stanza pipeline (id)...")
    stanza.download('id', verbose=False)
    _nlp_stanza = stanza.Pipeline(lang='id', processors='tokenize', verbose=False)
    print("      ✓ Stanza siap")

    # ── 3. Video Embeddings ───────────────────────────────────────
    print("[3/5] Memuat video embeddings...")
    vid_emb_path  = OUTPUT_DIR / 'video_embeddings.npy'
    vid_meta_path = OUTPUT_DIR / 'video_metadata.csv'

    if not vid_emb_path.exists():
        raise FileNotFoundError(
            f"\n❌ File 'video_embeddings.npy' tidak ditemukan di '{OUTPUT_DIR}'\n"
            "   Jalankan ulang cell Bagian 12 pada main.ipynb untuk menyimpan file ini."
        )

    _video_embeddings = np.load(str(vid_emb_path))
    _video_metadata   = pd.read_csv(str(vid_meta_path))
    # Normalisasi video embeddings sekali saja
    _video_embeddings = normalize(_video_embeddings, norm='l2')
    print(f"      ✓ Video embeddings: {_video_embeddings.shape}")

    # ── 4. Channel Matrix ─────────────────────────────────────────
    print("[4/5] Memuat channel matrix...")
    ch_mat_path  = OUTPUT_DIR / 'channel_matrix.npy'
    ch_name_path = OUTPUT_DIR / 'channel_names.csv'

    _channel_matrix = np.load(str(ch_mat_path))
    _channel_names  = pd.read_csv(str(ch_name_path))['nama_channel'].tolist()
    _channel_matrix = normalize(_channel_matrix, norm='l2')
    print(f"      ✓ Channel matrix: {_channel_matrix.shape}")

    # ── 5. Metadata & Categories ──────────────────────────────────
    print("[5/5] Memuat metadata dataset...")
    df_raw = pd.read_json(str(DATA_JSON_PATH))
    ch_unique = df_raw.drop_duplicates(subset='nama_channel').set_index('nama_channel')

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

    _categories = sorted(df_raw['kategori'].dropna().unique().tolist())
    print(f"      ✓ Kategori: {_categories}")

    print(f"\n{'='*55}")
    print("  ✅ Recommender siap digunakan!")
    print(f"{'='*55}\n")


# ═════════════════════════════════════════════════════════════════════════════
# PREPROCESSING PIPELINE (identik dengan notebook)
# ═════════════════════════════════════════════════════════════════════════════

def _text_cleaning(text):
    """Tahap 1: Hapus emoji, simbol non-standar, encoding rusak."""
    if not isinstance(text, str):
        return ''
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002600-\U000026FF"
        "\U00002700-\U000027BF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "\U00002300-\U000023FF"
        "]+",
        flags=re.UNICODE
    )
    text = emoji_pattern.sub(' ', text)
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', ' ', text)
    text = re.sub(r'[^\w\s.,?!\-()/@#%+=\'"":;]', ' ', text, flags=re.UNICODE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _case_folding(text):
    """Tahap 2: Lowercase."""
    return text.lower() if isinstance(text, str) else ''


def _tokenize_stanza(text):
    """Tahap 3: Tokenisasi dengan Stanza Indonesia."""
    global _nlp_stanza
    if not text or not text.strip():
        return text
    doc    = _nlp_stanza(text)
    tokens = [token.text for sent in doc.sentences for token in sent.tokens]
    return ' '.join(tokens)


def _remove_stopwords(text):
    """Tahap 4: Hapus stopwords Bahasa Indonesia."""
    if not isinstance(text, str) or not text.strip():
        return text
    tokens   = text.split()
    filtered = [t for t in tokens if t.lower() not in INDONESIAN_STOPWORDS and len(t) >= 2]
    return ' '.join(filtered) if filtered else text


def preprocess(text):
    """Pipeline lengkap: cleaning → case folding → tokenize Stanza → stopwords."""
    return _remove_stopwords(
        _tokenize_stanza(
            _case_folding(
                _text_cleaning(text)
            )
        )
    )


def _get_embedding(processed_text):
    """
    Attention-weighted Mean Pooling IndoBERT embedding (identik dengan notebook Bagian 7).
    Returns np.ndarray shape (768,), sudah L2-normalized.
    """
    global _tokenizer, _model

    inputs = _tokenizer(
        processed_text,
        return_tensors='pt',
        max_length=128,
        truncation=True,
        padding=True
    )
    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = _model(**inputs)

    token_embs   = outputs.last_hidden_state           # (1, L, 768)
    attn_mask    = inputs['attention_mask']             # (1, L)
    mask_exp     = attn_mask.unsqueeze(-1).expand(token_embs.size()).float()
    sum_emb      = torch.sum(token_embs * mask_exp, dim=1)
    sum_mask     = torch.clamp(mask_exp.sum(dim=1), min=1e-9)
    mean_emb     = (sum_emb / sum_mask).cpu().numpy()[0]  # (768,)
    return normalize(mean_emb.reshape(1, -1), norm='l2')[0]


# ═════════════════════════════════════════════════════════════════════════════
# RECOMMENDATION FUNCTIONS
# ═════════════════════════════════════════════════════════════════════════════

def recommend(query, mode='video', category=None, top_k=5):
    """
    Fungsi rekomendasi utama.

    Parameters
    ----------
    query    : str  – input query dari pengguna
    mode     : str  – 'video' atau 'channel'
    category : str  – nama kategori filter; None/'Semua' = tanpa filter
    top_k    : int  – jumlah hasil yang dikembalikan

    Returns
    -------
    dict – { results, query_processed, query_original, mode, category }
    """
    if not query or not query.strip():
        return {'error': 'Query tidak boleh kosong'}

    processed = preprocess(query)
    query_emb = _get_embedding(processed)   # (768,) L2-normalized

    use_all = (not category) or category.strip() in ('Semua', 'Semua Kategori', '')

    if mode == 'video':
        results = _recommend_videos(query_emb, category if not use_all else None, top_k)
    else:
        results = _recommend_channels(query_emb, category if not use_all else None, top_k)

    return {
        'results'         : results,
        'query_original'  : query,
        'query_processed' : processed,
        'mode'            : mode,
        'category'        : category or 'Semua',
    }


def _recommend_videos(query_emb, category, top_k):
    """Rekomendasi Top-K judul video berdasarkan cosine similarity."""
    global _video_embeddings, _video_metadata

    df   = _video_metadata
    embs = _video_embeddings

    # Filter kategori
    if category:
        mask = df['kategori'] == category
        df   = df[mask].reset_index(drop=True)
        embs = embs[mask.values]

    if len(df) == 0:
        return []

    sims    = cosine_similarity(query_emb.reshape(1, -1), embs)[0]
    top_idx = np.argsort(sims)[::-1][:top_k]

    results = []
    for rank, i in enumerate(top_idx, start=1):
        row = df.iloc[i]
        results.append({
            'rank'            : rank,
            'judul'           : str(row.get('judul', '')),
            'nama_channel'    : str(row.get('nama_channel', '')),
            'kategori'        : str(row.get('kategori', '')),
            'jumlah_tayangan' : _fmt_number(row.get('jumlah_tayangan', 0)),
            'tanggal_upload'  : str(row.get('tanggal_upload', '')),
            'link'            : str(row.get('link', '#')),
            'link_channel'    : str(row.get('link_channel', '#')),
            'similarity_score': round(float(sims[i]), 4),
        })
    return results


def _recommend_channels(query_emb, category, top_k):
    """Rekomendasi Top-K channel beserta judul video mirip per channel."""
    global _channel_matrix, _channel_names, _channel_info
    global _video_embeddings, _video_metadata

    ch_names = _channel_names
    ch_mat   = _channel_matrix

    # Filter kategori
    if category:
        filtered = [
            (i, ch) for i, ch in enumerate(ch_names)
            if _channel_info.get(ch, {}).get('kategori') == category
        ]
        if not filtered:
            return []
        f_idx, ch_names = zip(*filtered)
        ch_names = list(ch_names)
        ch_mat   = ch_mat[list(f_idx)]

    sims    = cosine_similarity(query_emb.reshape(1, -1), ch_mat)[0]
    top_idx = np.argsort(sims)[::-1][:top_k]

    results = []
    for rank, i in enumerate(top_idx, start=1):
        ch   = ch_names[i]
        info = _channel_info.get(ch, {})

        # Top-3 video dari channel ini yang paling mirip dengan query
        ch_mask    = _video_metadata['nama_channel'] == ch
        ch_vid_df  = _video_metadata[ch_mask].reset_index(drop=True)
        ch_vid_emb = _video_embeddings[ch_mask.values]

        top_vids = []
        if len(ch_vid_df) > 0:
            vid_sims = cosine_similarity(query_emb.reshape(1, -1), ch_vid_emb)[0]
            for vi in np.argsort(vid_sims)[::-1][:3]:
                v = ch_vid_df.iloc[vi]
                top_vids.append({
                    'judul'            : str(v.get('judul', '')),
                    'link'             : str(v.get('link', '#')),
                    'similarity_judul' : round(float(vid_sims[vi]), 4),
                })

        results.append({
            'rank'             : rank,
            'nama_channel'     : ch,
            'kategori'         : info.get('kategori', '-'),
            'jumlah_pelanggan' : _fmt_number(info.get('jumlah_pelanggan', 0)),
            'link_channel'     : info.get('link_channel', '#'),
            'similarity_score' : round(float(sims[i]), 4),
            'top_videos'       : top_vids,
        })
    return results


def get_categories():
    """Return list kategori dari dataset."""
    return _categories or []


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
