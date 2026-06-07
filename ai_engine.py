"""
DigiSurat AI Engine
Pipeline: upload dataset → preprocess → TF-IDF → train NB & KNN → save .pkl
"""

import json
import os
import re
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory  # type: ignore
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory  # type: ignore
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.neighbors import KNeighborsClassifier

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'models')
DATASETS_DIR = os.path.join(BASE_DIR, 'datasets')
METADATA_PATH = os.path.join(MODELS_DIR, 'metadata.json')

VECTORIZER_PATH = os.path.join(MODELS_DIR, 'tfidf_vectorizer.pkl')
NB_MODEL_PATH = os.path.join(MODELS_DIR, 'naive_bayes.pkl')
KNN_MODEL_PATH = os.path.join(MODELS_DIR, 'knn.pkl')

DEFAULT_CONFIG = {
    'vectorizer': 'tfidf',
    'knn_k': 11,
    'knn_metric': 'euclidean',
    'nb_alpha': 1.0,
    'active_param': 'preprocessing',
}

VALID_ACTIVE_PARAMS = {'preprocessing', 'knn', 'naive_bayes'}
VALID_TARGETS = {'preprocessing', 'knn', 'naive_bayes', 'both'}

TEXT_COLUMNS = ['teks', 'text', 'perihal', 'isi', 'content']
LABEL_COLUMNS = ['kategori', 'label', 'category', 'kelas']


def ensure_dirs():
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(DATASETS_DIR, exist_ok=True)


def _get_stemmer():
    return StemmerFactory().create_stemmer()


def _get_stopwords():
    return StopWordRemoverFactory().create_stop_word_remover()


def preprocess_text(text):
    if not isinstance(text, str):
        text = str(text) if text is not None else ''
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    if not text:
        return ''
    stopwords = _get_stopwords()
    stemmer = _get_stemmer()
    filtered = stopwords.remove(text)
    tokens = [t for t in filtered.split() if t]
    return ' '.join(stemmer.stem(t) for t in tokens)


def load_metadata():
    ensure_dirs()
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'trained': False,
        'last_trained': None,
        'total_samples': 0,
        'config': DEFAULT_CONFIG.copy(),
        'metrics': {},
        'best_model': None,
        'labels': [],
    }


def save_metadata(metadata):
    ensure_dirs()
    with open(METADATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def _detect_columns(df):
    text_col = next((c for c in TEXT_COLUMNS if c in df.columns), None)
    label_col = next((c for c in LABEL_COLUMNS if c in df.columns), None)

    if text_col and label_col:
        return text_col, label_col

    cols_lower = {c.lower(): c for c in df.columns}
    text_col = next((cols_lower[k] for k in TEXT_COLUMNS if k in cols_lower), None)
    label_col = next((cols_lower[k] for k in LABEL_COLUMNS if k in cols_lower), None)

    if text_col and label_col:
        return text_col, label_col

    if len(df.columns) >= 2:
        return df.columns[0], df.columns[1]

    raise ValueError(
        'Format dataset tidak valid. Kolom wajib: perihal/teks + kategori/label.'
    )


def load_dataset(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.csv':
        df = pd.read_csv(file_path)
    elif ext in ('.xlsx', '.xls'):
        df = pd.read_excel(file_path)
    elif ext == '.json':
        df = pd.read_json(file_path)
    else:
        raise ValueError('Format file tidak didukung. Gunakan CSV, XLSX, atau JSON.')

    text_col, label_col = _detect_columns(df)
    df = df[[text_col, label_col]].copy()
    df.columns = ['teks', 'kategori']
    df['teks'] = df['teks'].astype(str).str.strip()
    df['kategori'] = df['kategori'].astype(str).str.strip()
    df = df[(df['teks'] != '') & (df['kategori'] != '')]
    df = df.drop_duplicates()

    if len(df) < 6:
        raise ValueError('Dataset minimal 6 baris data valid untuk pelatihan.')

    return df


def _build_vectorizer(config):
    method = config.get('vectorizer', 'tfidf')
    if method == 'count':
        return CountVectorizer()
    if method == 'bow':
        return CountVectorizer(binary=True)
    return TfidfVectorizer()


def _metric_kwargs(y_test):
    labels = sorted(set(y_test))
    average = 'weighted' if len(labels) > 2 else 'binary'
    return {'average': average, 'zero_division': 0, 'labels': labels}


def _evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    kwargs = _metric_kwargs(y_test)
    return {
        'accuracy': round(accuracy_score(y_test, y_pred), 4),
        'precision': round(precision_score(y_test, y_pred, **kwargs), 4),
        'recall': round(recall_score(y_test, y_pred, **kwargs), 4),
        'f1': round(f1_score(y_test, y_pred, **kwargs), 4),
    }


def _pick_best_model(metrics):
    if not metrics:
        return None
    scores = {}
    for name, m in metrics.items():
        scores[name] = (m['f1'] + m['accuracy']) / 2
    return max(scores, key=scores.get)


def _resolve_train_targets(target):
    target = target or 'preprocessing'
    if target not in VALID_TARGETS:
        raise ValueError('Parameter aktif tidak valid.')
    if target == 'preprocessing':
        return {'naive_bayes', 'knn'}
    if target == 'both':
        return {'naive_bayes', 'knn'}
    return {target}


def train_models(dataset_path, config=None, target=None):
    ensure_dirs()
    config = {**DEFAULT_CONFIG, **(config or {})}
    train_targets = _resolve_train_targets(target or config.get('active_param'))
    df = load_dataset(dataset_path)

    df['teks_bersih'] = df['teks'].apply(preprocess_text)
    df = df[df['teks_bersih'] != '']
    if len(df) < 6:
        raise ValueError('Setelah preprocessing, data latih kurang dari 6 baris.')

    X_raw = df['teks_bersih'].tolist()
    y = df['kategori'].tolist()
    labels = sorted(set(y))

    test_size = 0.2 if len(df) >= 15 else max(1 / len(df), 0.15)
    stratify = y if len(set(y)) > 1 and min(pd.Series(y).value_counts()) >= 2 else None

    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X_raw, y, test_size=test_size, random_state=42, stratify=stratify
    )

    vectorizer = _build_vectorizer(config)
    X_train = vectorizer.fit_transform(X_train_raw)
    X_test = vectorizer.transform(X_test_raw)
    joblib.dump(vectorizer, VECTORIZER_PATH)

    existing = load_metadata()
    metrics = dict(existing.get('metrics', {}))

    if 'naive_bayes' in train_targets:
        nb_model = MultinomialNB(alpha=float(config.get('nb_alpha', 1.0)))
        nb_model.fit(X_train, y_train)
        joblib.dump(nb_model, NB_MODEL_PATH)
        metrics['naive_bayes'] = _evaluate_model(nb_model, X_test, y_test)
    else:
        metrics.pop('naive_bayes', None)
        if os.path.exists(NB_MODEL_PATH):
            os.remove(NB_MODEL_PATH)

    if 'knn' in train_targets:
        knn_metric = config.get('knn_metric', 'euclidean')
        metric_map = {
            'euclidean': 'minkowski',
            'manhattan': 'manhattan',
            'cosine': 'cosine',
        }
        knn_model = KNeighborsClassifier(
            n_neighbors=int(config.get('knn_k', 11)),
            metric=metric_map.get(knn_metric, 'minkowski'),
        )
        knn_model.fit(X_train, y_train)
        joblib.dump(knn_model, KNN_MODEL_PATH)
        metrics['knn'] = _evaluate_model(knn_model, X_test, y_test)
    else:
        metrics.pop('knn', None)
        if os.path.exists(KNN_MODEL_PATH):
            os.remove(KNN_MODEL_PATH)

    best_model = _pick_best_model(metrics)
    trained_algorithms = [name for name in ('naive_bayes', 'knn') if name in metrics]

    metadata = {
        'trained': len(trained_algorithms) > 0,
        'last_trained': datetime.now().strftime('%d %B %Y, %H:%M'),
        'total_samples': len(df),
        'config': config,
        'metrics': metrics,
        'best_model': best_model,
        'labels': labels,
        'dataset_file': os.path.basename(dataset_path),
        'last_trained_target': sorted(train_targets),
    }
    save_metadata(metadata)

    return metadata


def get_config():
    metadata = load_metadata()
    return metadata.get('config', DEFAULT_CONFIG.copy())


def update_config(new_config, active_param=None):
    metadata = load_metadata()
    config = {**DEFAULT_CONFIG, **metadata.get('config', {}), **new_config}

    if active_param:
        if active_param not in VALID_ACTIVE_PARAMS:
            raise ValueError('Parameter aktif tidak valid.')
        config['active_param'] = active_param

    metadata['config'] = config
    save_metadata(metadata)
    return config


def save_active_param_config(active_param, values):
    if active_param not in VALID_ACTIVE_PARAMS:
        raise ValueError('Parameter aktif tidak valid.')

    payload = {'active_param': active_param}
    if active_param == 'preprocessing':
        payload['vectorizer'] = values.get('vectorizer', 'tfidf')
    elif active_param == 'knn':
        payload['knn_k'] = int(values.get('knn_k', 11))
        payload['knn_metric'] = values.get('knn_metric', 'euclidean')
    elif active_param == 'naive_bayes':
        payload['nb_alpha'] = float(values.get('nb_alpha', 1.0))

    return update_config(payload, active_param=active_param)


def get_status():
    metadata = load_metadata()
    return {
        'trained': metadata.get('trained', False),
        'last_trained': metadata.get('last_trained'),
        'total_samples': metadata.get('total_samples', 0),
        'metrics': metadata.get('metrics', {}),
        'best_model': metadata.get('best_model'),
        'config': metadata.get('config', DEFAULT_CONFIG.copy()),
        'labels': metadata.get('labels', []),
        'dataset_file': metadata.get('dataset_file'),
    }


def _load_artifacts():
    if not os.path.exists(VECTORIZER_PATH):
        return None, None, None

    vectorizer = joblib.load(VECTORIZER_PATH)
    nb_model = joblib.load(NB_MODEL_PATH) if os.path.exists(NB_MODEL_PATH) else None
    knn_model = joblib.load(KNN_MODEL_PATH) if os.path.exists(KNN_MODEL_PATH) else None

    if nb_model is None and knn_model is None:
        return None, None, None

    return vectorizer, nb_model, knn_model


def classify_text(text, model_name=None):
    metadata = load_metadata()
    if not metadata.get('trained'):
        return {'status': 'error', 'message': 'Model belum dilatih. Latih dataset di Pengaturan AI.'}

    vectorizer, nb_model, knn_model = _load_artifacts()
    if vectorizer is None:
        return {'status': 'error', 'message': 'File model (.pkl) tidak ditemukan.'}

    cleaned = preprocess_text(text)
    if not cleaned:
        return {'status': 'error', 'message': 'Teks tidak valid untuk klasifikasi.'}

    X = vectorizer.transform([cleaned])
    model_name = model_name or metadata.get('best_model')

    if model_name == 'naive_bayes' and nb_model is not None:
        model = nb_model
        display_name = 'Naive Bayes'
    elif knn_model is not None:
        model = knn_model
        display_name = 'K-NN'
        model_name = 'knn'
    elif nb_model is not None:
        model = nb_model
        display_name = 'Naive Bayes'
        model_name = 'naive_bayes'
    else:
        return {'status': 'error', 'message': 'Model klasifikasi belum tersedia.'}

    prediction = str(model.predict(X)[0])
    confidence = None
    if hasattr(model, 'predict_proba'):
        proba = model.predict_proba(X)[0]
        confidence = round(float(np.max(proba)) * 100, 1)

    return {
        'status': 'success',
        'kategori': prediction,
        'model': model_name,
        'model_display': display_name,
        'confidence': confidence,
    }
