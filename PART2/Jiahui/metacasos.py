import json, re
from collections import Counter
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


import umap
import hdbscan
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer


DATA_PATH = "cbr_recipes_database.json"

# ---------- 1) Cargar ----------
with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

recipes = data["recipes"]  # <- OJO: aquí está la lista real
df = pd.DataFrame(recipes)

# ---------- 2) Normalización ----------
def norm(s: str) -> str:
    if s is None:
        return ""
    s = str(s).lower().strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^a-z0-9áéíóúüñ\s/\-]", "", s)  # conserva / y -
    return s

def split_taxonomy(value: str):
    """
    Convierte "Italiana/Toscana" -> ["italiana", "toscana"]
    Convierte "Fusión Americana-India" -> ["fusion", "americana", "india"]
    """
    v = norm(value)
    if not v:
        return []
    v = v.replace("fusión", "fusion")  # por si viene con tilde
    parts = re.split(r"[\/\-]", v)
    parts = [p.strip() for p in parts if p.strip()]
    # si es fusión, añade token explícito
    out = []
    if "fusion" in v:
        out.append("fusion")
    out.extend(parts)
    # dedup manteniendo orden
    seen = set()
    dedup = []
    for p in out:
        if p not in seen:
            seen.add(p)
            dedup.append(p)
    return dedup

ING_STOP = {"salt", "water", "pepper", "olive oil", "sugar", "flour", "butter"}

def clean_ingredients(lst):
    lst = lst or []
    out, seen = [], set()
    for x in lst:
        t = norm(x)
        if not t or t in ING_STOP:
            continue
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out

# ---------- 3) Documento: SOLO cultura + estilo + ingredientes ----------
# Truco: repetir cultura/estilo para que "pesen más" en el embedding
CULTURE_WEIGHT = 3
STYLE_WEIGHT = 3
ING_LIMIT = 20

def build_doc(row):
    cultura_tokens = split_taxonomy(row.get("cultura", ""))
    estilo_tokens = split_taxonomy(row.get("estilo_cocina", ""))
    ing_tokens = clean_ingredients(row.get("ingredients", []))[:ING_LIMIT]

    culture_part = " ".join([f"cultura:{t}" for t in cultura_tokens] * CULTURE_WEIGHT)
    style_part = " ".join([f"estilo:{t}" for t in estilo_tokens] * STYLE_WEIGHT)
    ing_part = " ".join([f"ing:{t}" for t in ing_tokens])

    return f"{culture_part} {style_part} {ing_part}".strip()

docs = df.apply(build_doc, axis=1).tolist()

# ---------- 4) Embeddings ----------
# Como tienes mezcla español (cultura/estilo) + inglés (ingredientes),
# usa modelo multilingual para que no “pierda” las etiquetas en español:
embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

embeddings = embedding_model.encode(
    docs,
    batch_size=32,
    show_progress_bar=True,
    normalize_embeddings=True
)

# ---------- 5) UMAP + HDBSCAN ----------
# OJO: tu JSON ahora tiene 30 recetas (según metadata). Con tan poco,
# HDBSCAN es sensible: usa min_cluster_size bajo.
umap_model = umap.UMAP(
    n_neighbors=8,       # más bajo para datasets pequeños
    n_components=5,
    metric="cosine",
    random_state=42
)

hdbscan_model = hdbscan.HDBSCAN(
    min_cluster_size=3,          # prueba 2-5 si son pocas recetas
    min_samples=1,              # menos outliers en datasets pequeños
    metric="euclidean",
    cluster_selection_method="eom",
    prediction_data=True
)

vectorizer_model = CountVectorizer(
    ngram_range=(1, 2),
    min_df=1,            # importante para evitar errores con pocos clusters
    max_df=0.95,
    token_pattern=r"(?u)\b[a-zA-Záéíóúüñ][a-zA-Z0-9áéíóúüñ:\-]+\b"
)

topic_model = BERTopic(
    umap_model=umap_model,
    hdbscan_model=hdbscan_model,
    vectorizer_model=vectorizer_model,
    calculate_probabilities=False,
    verbose=True
)

topics, _ = topic_model.fit_transform(docs, embeddings)
df["topic"] = topics


# ---------- 5.1) Visualización 2D con UMAP ----------
umap_vis = umap.UMAP(
    n_neighbors=8,      # ponlo igual que tu umap_model (o 10-20 si crece el dataset)
    n_components=2,
    metric="cosine",
    random_state=42
)
coords_2d = umap_vis.fit_transform(embeddings)

df["umap_x"] = coords_2d[:, 0]
df["umap_y"] = coords_2d[:, 1]

# Plot
plt.figure(figsize=(10, 7))

# outliers
mask_out = df["topic"] == -1
plt.scatter(
    df.loc[mask_out, "umap_x"],
    df.loc[mask_out, "umap_y"],
    s=60, alpha=0.35, marker="x",
    label="outliers (-1)"
)

# clusters
for t in sorted([x for x in df["topic"].unique() if x != -1]):
    m = df["topic"] == t
    plt.scatter(df.loc[m, "umap_x"], df.loc[m, "umap_y"], s=70, alpha=0.85, label=f"topic {t}")

# (Opcional) Etiquetas: útil si tienes pocas recetas (como tu dataset de 30)
for _, r in df.iterrows():
    title = str(r.get("title", ""))[:18]
    plt.text(r["umap_x"], r["umap_y"], title, fontsize=8, alpha=0.8)

plt.title("Clusters (BERTopic/HDBSCAN) proyectados con UMAP 2D")
plt.xlabel("UMAP-1")
plt.ylabel("UMAP-2")
plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
plt.tight_layout()
plt.show()


print(topic_model.get_topic_info())

# ---------- 6) Metacasos (representante + perfil) ----------
def cosine_distance(a, b):
    return 1.0 - float(np.dot(a, b))  # embeddings normalizados

def to_jsonable(x):
    import numpy as np
    import pandas as pd
    if isinstance(x, (np.integer,)): return int(x)
    if isinstance(x, (np.floating,)): return float(x)
    if isinstance(x, (np.ndarray,)): return x.tolist()
    if isinstance(x, dict): return {k: to_jsonable(v) for k, v in x.items()}
    if isinstance(x, list): return [to_jsonable(v) for v in x]
    if isinstance(x, (pd.Timestamp,)): return x.isoformat()
    return x

meta_cases = []
for topic_id in sorted(df["topic"].unique()):
    idxs = df.index[df["topic"] == topic_id].to_list()
    E = embeddings[idxs]

    centroid = E.mean(axis=0)
    centroid = centroid / (np.linalg.norm(centroid) + 1e-12)

    dists = [cosine_distance(E[i], centroid) for i in range(len(idxs))]
    rep_local = int(np.argmin(dists))
    rep_idx = idxs[rep_local]

    keywords = [w for (w, _) in topic_model.get_topic(topic_id)][:12]

    # Perfil: cultura, estilo, top ingredientes
    cultura_top = df.loc[idxs, "cultura"].value_counts().head(5).to_dict()
    estilo_top = df.loc[idxs, "estilo_cocina"].value_counts().head(5).to_dict()

    ing_all = []
    for lst in df.loc[idxs, "ingredients"].tolist():
        ing_all += clean_ingredients(lst)
    ing_top = dict(Counter(ing_all).most_common(12))

    meta_cases.append({
        "topic_id": int(topic_id),
        "size": int(len(idxs)),
        "centroid_embedding": centroid.tolist(),
        "keywords": keywords,
        "profile": {
            "cultura_top": cultura_top,
            "estilo_cocina_top": estilo_top,
            "ingredients_top": ing_top
        },
        "representative_recipe": {
            "recipe_id": int(df.loc[rep_idx, "recipe_id"]),
            "title": df.loc[rep_idx, "title"],
            "cultura": df.loc[rep_idx, "cultura"],
            "estilo_cocina": df.loc[rep_idx, "estilo_cocina"],
            "ingredients": df.loc[rep_idx, "ingredients"],
        },
        "member_recipe_ids": [int(x) for x in df.loc[idxs, "recipe_id"].tolist()]
    })

with open("meta_cases_cultura_estilo.json", "w", encoding="utf-8") as f:
    json.dump(to_jsonable(meta_cases), f, ensure_ascii=False, indent=2)

print("Metacasos:", len(meta_cases), "| Outliers:", int((df["topic"] == -1).sum()))
