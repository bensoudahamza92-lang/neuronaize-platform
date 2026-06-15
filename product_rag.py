from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from product_catalog import CATALOG_REQUIRED_COLUMNS


UNAVAILABLE_MESSAGE = "Cette information n’est pas disponible dans le catalogue fourni."


@dataclass
class ProductRAGIndex:
    """Local catalogue index for demo RAG without external APIs."""

    catalog: pd.DataFrame
    vectorizer: TfidfVectorizer
    matrix: object
    documents: list[str]
    faiss_index: object | None = None


def build_product_document(row: pd.Series) -> str:
    parts = []
    for column in CATALOG_REQUIRED_COLUMNS:
        value = row.get(column, "")
        if pd.notna(value) and str(value).strip():
            parts.append(f"{column}: {value}")
    return "\n".join(parts)


def build_product_rag_index(catalog: pd.DataFrame) -> ProductRAGIndex:
    """Build a local product catalogue index.

    The demo uses TF-IDF embeddings locally. If FAISS is installed, it is used
    for vector search over the dense normalized vectors; otherwise cosine
    similarity is computed directly with scikit-learn.
    """

    documents = [build_product_document(row) for _, row in catalog.iterrows()]
    if not documents:
        raise ValueError("Le catalogue produit est vide.")

    vectorizer = TfidfVectorizer(strip_accents="unicode", lowercase=True, ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(documents)

    faiss_index = None
    try:
        import faiss  # type: ignore

        dense = matrix.toarray().astype("float32")
        norms = np.linalg.norm(dense, axis=1, keepdims=True)
        dense = dense / np.maximum(norms, 1e-12)
        faiss_index = faiss.IndexFlatIP(dense.shape[1])
        faiss_index.add(dense)
    except Exception:
        faiss_index = None

    return ProductRAGIndex(
        catalog=catalog.reset_index(drop=True),
        vectorizer=vectorizer,
        matrix=matrix,
        documents=documents,
        faiss_index=faiss_index,
    )


def retrieve_product_context(
    index: ProductRAGIndex | None,
    question: str,
    product_source_column: str | None = None,
    top_k: int = 2,
) -> pd.DataFrame:
    if index is None or not question.strip():
        return pd.DataFrame()

    catalog = index.catalog
    candidate_catalog = catalog
    candidate_offsets = list(range(len(catalog)))

    if product_source_column:
        mask = catalog["Colonne source bddf2"].astype(str).str.strip() == str(product_source_column).strip()
        if mask.any():
            candidate_catalog = catalog[mask].reset_index(drop=True)
            candidate_offsets = catalog.index[mask].tolist()

    query = index.vectorizer.transform([question])

    if index.faiss_index is not None and candidate_catalog is catalog:
        dense_query = query.toarray().astype("float32")
        dense_query = dense_query / np.maximum(np.linalg.norm(dense_query, axis=1, keepdims=True), 1e-12)
        scores, positions = index.faiss_index.search(dense_query, min(top_k, len(catalog)))
        rows = catalog.iloc[positions[0]].copy()
        rows["_score"] = scores[0]
        return rows

    matrix = index.matrix[candidate_offsets]
    scores = cosine_similarity(query, matrix).flatten()
    if not np.any(scores > 0):
        return pd.DataFrame()
    selected = np.argsort(scores)[::-1][:top_k]
    rows = candidate_catalog.iloc[selected].copy()
    rows["_score"] = scores[selected]
    return rows


def answer_from_catalog(
    index: ProductRAGIndex | None,
    question: str,
    product_source_column: str | None = None,
) -> str:
    """Answer strictly from the indexed catalogue fields."""

    context = retrieve_product_context(index, question, product_source_column=product_source_column, top_k=1)
    if context.empty:
        return UNAVAILABLE_MESSAGE

    row = context.iloc[0]
    normalized = question.lower()

    field_map = {
        "Conditions d’éligibilité": ["elig", "élig", "condition"],
        "Avantages": ["avantage", "benefit", "bénéfice"],
        "Limites / points de vigilance": ["limite", "vigilance", "risque", "watch"],
        "Arguments commerciaux": ["argument", "commercial", "vente", "sales"],
        "Description": ["description", "quoi", "what", "présente", "presente"],
    }

    selected_fields = [
        field
        for field, tokens in field_map.items()
        if any(token in normalized for token in tokens)
        and pd.notna(row.get(field, ""))
        and str(row.get(field, "")).strip()
    ]

    if not selected_fields:
        broad_catalog_tokens = [
            "résume",
            "resume",
            "présente",
            "presente",
            "explique",
            "detail",
            "détail",
            "information",
            "produit",
            "product",
        ]
        if not any(token in normalized for token in broad_catalog_tokens):
            return UNAVAILABLE_MESSAGE
        selected_fields = [
            field
            for field in ["Description", "Avantages", "Conditions d’éligibilité"]
            if pd.notna(row.get(field, "")) and str(row.get(field, "")).strip()
        ]

    if not selected_fields:
        return UNAVAILABLE_MESSAGE

    parts = [f"{field} : {row[field]}" for field in selected_fields]
    return "\n\n".join(parts)
