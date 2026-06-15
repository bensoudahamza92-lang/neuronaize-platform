"""Business logic for a banking recommendation demo.

The module trains a local KMedoids clustering model on customer features, then
recommends products that are common among similar customers in the same cluster.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import OrdinalEncoder, StandardScaler
from sklearn_extra.cluster import KMedoids

from shared_models import RecommendationResult, WorkflowState


PRODUCT_PREFIX = "Produit -"
DEFAULT_CLIENT_CODE_CANDIDATES = (
    "Code client",
    "Code Client",
    "CODE CLIENT",
    "Client",
    "client",
    "ID Client",
    "Id client",
    "Identifiant client",
)


@dataclass
class BankingRecommender:
    """KMedoids-based recommendation engine for customer/product data."""

    threshold: float = 0.30
    min_clusters: int = 3
    max_clusters: int = 10
    random_state: int = 42

    product_columns: list[str] | None = None
    feature_columns: list[str] | None = None
    identifier_columns: list[str] | None = None
    client_code_column: object | None = None
    numeric_columns: list[str] | None = None
    categorical_columns: list[str] | None = None
    numeric_medians: dict[str, float] | None = None
    categorical_modes: dict[str, object] | None = None
    encoder: OrdinalEncoder | None = None
    scaler: StandardScaler | None = None
    model: KMedoids | None = None
    cluster_summary_: pd.DataFrame | None = None
    training_data_: pd.DataFrame | None = None
    selected_n_clusters_: int | None = None
    inertia_diagnostics_: pd.DataFrame | None = None
    cluster_selection_method_: str | None = None

    def fit(self, data: pd.DataFrame) -> "BankingRecommender":
        """Fit preprocessing, choose a cluster count, train KMedoids, and summarize."""

        self._validate_training_data(data)
        df = data.copy()
        self.training_data_ = df

        self.product_columns = detect_product_columns(df)
        self.client_code_column = str(df.columns[0])
        self.identifier_columns = [df.columns[0]]
        self.feature_columns = [
            col
            for col in df.columns
            if col not in self.product_columns and col not in self.identifier_columns
        ]

        if not self.feature_columns:
            raise ValueError("Aucune colonne de caractéristique client n'a été détectée.")

        x = self._fit_transform_features(df)
        n_clusters, diagnostics, method = select_optimal_k_by_inertia(
            x,
            min_clusters=self.min_clusters,
            max_clusters=self.max_clusters,
            random_state=self.random_state,
        )
        self.selected_n_clusters_ = n_clusters
        self.inertia_diagnostics_ = diagnostics
        self.cluster_selection_method_ = method

        self.model = train_clustering_model(x, n_clusters, self.random_state)
        clusters = self.model.labels_
        df["_cluster"] = clusters
        self.training_data_ = df
        self.cluster_summary_ = build_cluster_summary(
            df,
            self.feature_columns,
            self.product_columns,
        )
        return self

    def predict_cluster(self, customer: pd.Series | pd.DataFrame) -> int:
        """Predict the cluster for one customer row."""

        self._ensure_fitted()
        row = _as_single_row(customer)
        x = self._transform_features(row)
        return int(self.model.predict(x)[0])

    def recommend(
        self,
        customer: pd.Series | pd.DataFrame,
        threshold: float | None = None,
    ) -> pd.DataFrame:
        """Return products owned above threshold in the predicted cluster and absent for the customer."""

        self._ensure_fitted()
        cutoff = self.threshold if threshold is None else threshold
        row = _as_single_row(customer)
        cluster_id = self.predict_cluster(row)

        cluster_rows = self.training_data_[self.training_data_["_cluster"] == cluster_id]
        product_rates = cluster_rows[self.product_columns].apply(_binary_series).mean()

        recommendations = []
        for product, score in product_rates.sort_values(ascending=False).items():
            owns_product = _is_owned(row.iloc[0].get(product, 0))
            if score >= cutoff and not owns_product:
                recommendations.append(
                    {
                        "Produit": product,
                        "Score %": round(float(score) * 100, 1),
                        "Source": f"Cluster {cluster_id} ({len(cluster_rows)} clients similaires)",
                        "Cluster": cluster_id,
                        "Clients similaires": len(cluster_rows),
                    }
                )

        return pd.DataFrame(
            recommendations,
            columns=["Produit", "Score %", "Source", "Cluster", "Clients similaires"],
        )

    def get_customer_by_code(self, code: object) -> pd.DataFrame:
        """Return a single customer row by the first-column client code."""

        self._ensure_fitted()
        if self.client_code_column is None:
            raise ValueError("Aucune colonne Code Client n'a été identifiée.")

        code_text = normalize_client_code(code)
        if not code_text:
            raise ValueError("Veuillez saisir un Code Client.")

        normalized_codes = self.training_data_[self.client_code_column].map(normalize_client_code)
        matches = self.training_data_[normalized_codes == code_text]
        if matches.empty:
            raise ValueError(f"Aucun client trouvé pour le code {code_text}.")
        return matches.iloc[[0]].drop(columns=["_cluster"], errors="ignore")

    def customer_profile(self, customer: pd.Series | pd.DataFrame) -> pd.DataFrame:
        """Return a display-friendly profile for one customer."""

        row = _as_single_row(customer).iloc[0]
        profile = row.drop(labels=["_cluster"], errors="ignore").to_frame("Valeur")
        profile.index.name = "Champ"
        return profile

    def save(self, path: str) -> None:
        """Persist the fitted recommender."""

        joblib.dump(self, path)

    @staticmethod
    def load(path: str) -> "BankingRecommender":
        """Load a persisted recommender."""

        return joblib.load(path)

    def _fit_transform_features(self, df: pd.DataFrame) -> np.ndarray:
        features = df[self.feature_columns].copy()
        self.numeric_columns = features.select_dtypes(include=[np.number]).columns.tolist()
        self.categorical_columns = [col for col in features.columns if col not in self.numeric_columns]

        numeric_part = pd.DataFrame(index=features.index)
        self.numeric_medians = {}
        for col in self.numeric_columns:
            values = pd.to_numeric(features[col], errors="coerce")
            median = float(values.median()) if not values.dropna().empty else 0.0
            self.numeric_medians[col] = median
            numeric_part[col] = values.fillna(median)

        categorical_part = pd.DataFrame(index=features.index)
        self.categorical_modes = {}
        for col in self.categorical_columns:
            values = features[col].astype("string").fillna("")
            mode = values.mode(dropna=True)
            fill_value = str(mode.iloc[0]) if not mode.empty else "Inconnu"
            self.categorical_modes[col] = fill_value
            categorical_part[col] = values.replace("", fill_value).fillna(fill_value)

        encoded = self._fit_encode_categories(categorical_part)
        matrix = np.hstack([numeric_part.to_numpy(dtype=float), encoded])
        self.scaler = StandardScaler()
        return self.scaler.fit_transform(matrix)

    def _transform_features(self, df: pd.DataFrame) -> np.ndarray:
        missing = [col for col in self.feature_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Colonnes de caractéristiques manquantes : {', '.join(missing)}")

        features = df[self.feature_columns].copy()
        numeric_part = pd.DataFrame(index=features.index)
        for col in self.numeric_columns:
            values = pd.to_numeric(features[col], errors="coerce")
            numeric_part[col] = values.fillna(self.numeric_medians[col])

        categorical_part = pd.DataFrame(index=features.index)
        for col in self.categorical_columns:
            values = features[col].astype("string").fillna("")
            categorical_part[col] = values.replace("", self.categorical_modes[col]).fillna(
                self.categorical_modes[col]
            )

        encoded = self._encode_categories(categorical_part)
        matrix = np.hstack([numeric_part.to_numpy(dtype=float), encoded])
        return self.scaler.transform(matrix)

    def _fit_encode_categories(self, categorical_part: pd.DataFrame) -> np.ndarray:
        if categorical_part.empty:
            return np.empty((len(categorical_part), 0))
        self.encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
        return self.encoder.fit_transform(categorical_part)

    def _encode_categories(self, categorical_part: pd.DataFrame) -> np.ndarray:
        if categorical_part.empty:
            return np.empty((len(categorical_part), 0))
        return self.encoder.transform(categorical_part)

    def _ensure_fitted(self) -> None:
        if self.model is None or self.training_data_ is None or self.cluster_summary_ is None:
            raise ValueError("Le modèle n'est pas encore entraîné. Lancez d'abord l'analyse.")

    def _validate_training_data(self, data: pd.DataFrame) -> None:
        if data is None or data.empty:
            raise ValueError("Le fichier chargé ne contient aucune donnée.")
        product_columns = detect_product_columns(data)
        if not product_columns:
            raise ValueError('Aucune colonne produit détectée. Les colonnes doivent commencer par "Produit -".')
        if len(data) < 2:
            raise ValueError("Il faut au moins deux clients pour entraîner le clustering.")


def detect_product_columns(data: pd.DataFrame) -> list[str]:
    """Find product ownership columns."""

    return [col for col in data.columns if str(col).startswith(PRODUCT_PREFIX)]


def detect_identifier_columns(columns: Iterable[str]) -> list[str]:
    """Detect customer identifiers that should not drive clustering."""

    detected = []
    for col in columns:
        normalized = str(col).strip().lower()
        if col in DEFAULT_CLIENT_CODE_CANDIDATES:
            detected.append(col)
        elif ("code" in normalized and "client" in normalized) or normalized in {"id", "client_id"}:
            detected.append(col)
    return detected


def find_client_code_column(data: pd.DataFrame) -> str | None:
    """Return the first column as the customer-code column."""

    if data is None or data.empty or len(data.columns) == 0:
        return None
    return str(data.columns[0])


def normalize_client_code(value: object) -> str:
    """Normalize Excel client codes for robust lookup.

    Excel often returns numeric identifiers as 123.0 while users type 123.
    """

    if pd.isna(value):
        return ""
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)) and float(value).is_integer():
        return str(int(value))

    text = str(value).strip()
    try:
        numeric = float(text)
        if numeric.is_integer():
            return str(int(numeric))
    except ValueError:
        pass
    return text


def execute_recommendation_component(state: WorkflowState) -> WorkflowState:
    """Execute C1 recommendation component for workflow usage.

    Expected state variables:
    - recommender: fitted BankingRecommender
    - customer or customer_df: one customer row as pandas DataFrame/Series
    - client_code: optional fallback when customer is not provided
    - threshold: optional recommendation threshold

    The Streamlit UI still calls BankingRecommender directly; this function is
    the workflow-compatible adapter around the existing behavior.
    """

    variables = dict(state.variables or {})
    recommender = variables.get("recommender")
    if recommender is None:
        raise ValueError("C1 Recommendation: variable 'recommender' manquante dans WorkflowState.")
    if not isinstance(recommender, BankingRecommender):
        raise TypeError("C1 Recommendation: 'recommender' doit être une instance de BankingRecommender.")

    customer = variables.get("customer")
    if customer is None:
        customer = variables.get("customer_df")
    if customer is None and variables.get("client_code") is not None:
        customer = recommender.get_customer_by_code(variables["client_code"])
    if customer is None:
        raise ValueError(
            "C1 Recommendation: fournir 'customer', 'customer_df' ou 'client_code' dans WorkflowState.variables."
        )

    threshold = variables.get("threshold")
    recommendations_df = recommender.recommend(customer, threshold=threshold)
    customer_row = _as_single_row(customer).iloc[0]
    client_code = normalize_client_code(customer_row.get(recommender.client_code_column, ""))

    results: list[RecommendationResult] = []
    for _, row in recommendations_df.iterrows():
        product_source_column = str(row.get("Produit", ""))
        cluster_id = int(row.get("Cluster", recommender.predict_cluster(customer)))
        score_percent = float(row.get("Score %", 0.0))
        similar_customers_count = int(row.get("Clients similaires", 0))
        product_name = product_source_column.replace(PRODUCT_PREFIX, "").strip()
        results.append(
            RecommendationResult(
                client_code=client_code,
                product_source_column=product_source_column,
                product_name=product_name,
                cluster_id=cluster_id,
                score_percent=score_percent,
                similar_customers_count=similar_customers_count,
                source=str(row.get("Source", "")),
                reason=(
                    "Produit non détenu par le client et fréquent chez les clients similaires "
                    f"du cluster {cluster_id}."
                ),
                metadata={"component": "C1", "threshold": threshold if threshold is not None else recommender.threshold},
            )
        )

    state.recommendations = results
    variables["recommendations_df"] = recommendations_df
    variables["recommendation_count"] = len(results)
    variables["recommendation_component"] = "C1"
    state.variables = variables
    state.current_node_id = "C1_RECOMMENDATION"
    state.updated_at = datetime.now()
    return state


def create_kmedoids_model(k: int, random_state: int = 42) -> KMedoids:
    """Create the KMedoids model used for diagnostics and final clustering."""

    return KMedoids(
        n_clusters=int(k),
        init="k-medoids++",
        metric="manhattan",
        random_state=random_state,
    )


def compute_kmedoids_inertias(
    x_scaled: np.ndarray,
    max_clusters: int,
    random_state: int = 42,
) -> tuple[list[int], list[float]]:
    """Compute KMedoids inertia for k=1..max_clusters."""

    n_rows = len(x_scaled)
    upper = max(1, min(int(max_clusters), n_rows))
    k_values = list(range(1, upper + 1))
    inertias: list[float] = []

    for k in k_values:
        model = create_kmedoids_model(k, random_state=random_state)
        model.fit(x_scaled)
        inertias.append(float(model.inertia_))

    return k_values, inertias


def detect_elbow_k(
    k_values: list[int],
    inertias: list[float],
    min_clusters: int = 3,
    fallback_k: int = 4,
) -> tuple[int, str]:
    """Detect the inertia elbow with KneeLocator, then a curvature fallback."""

    if not k_values or not inertias:
        return fallback_k, "fallback"

    try:
        from kneed import KneeLocator

        knee = KneeLocator(
            k_values,
            inertias,
            curve="convex",
            direction="decreasing",
        )
        selected_k = knee.elbow
        if selected_k is not None and int(selected_k) >= min_clusters:
            return int(selected_k), "knee_locator"
    except Exception:
        pass

    diff1 = np.diff(inertias)
    diff2 = np.diff(diff1)

    if len(diff2) > 0:
        threshold = np.percentile(diff2, 80)
        candidate_elbows = np.argwhere(diff2 > threshold).flatten() + 2
        candidate_elbows = [int(k) for k in candidate_elbows if int(k) >= min_clusters]

        if candidate_elbows:
            return max(candidate_elbows), "curvature"

    return fallback_k, "fallback"


def select_optimal_k_by_inertia(
    x_scaled: np.ndarray,
    min_clusters: int = 3,
    max_clusters: int = 10,
    random_state: int = 42,
) -> tuple[int, pd.DataFrame, str]:
    """Select the cluster count from the elbow of the KMedoids inertia curve."""

    n_rows = len(x_scaled)
    if n_rows < 4:
        selected_k = min(max(1, n_rows), max_clusters)
        k_values, inertias = compute_kmedoids_inertias(x_scaled, selected_k, random_state)
        diagnostics = pd.DataFrame({"k": k_values, "inertia": inertias})
        return selected_k, diagnostics, "small_dataset"

    effective_min = max(2, min(int(min_clusters), n_rows - 1))
    effective_max = max(effective_min, min(int(max_clusters), n_rows - 1))
    k_values, inertias = compute_kmedoids_inertias(
        x_scaled,
        max_clusters=effective_max,
        random_state=random_state,
    )

    selected_k, method = detect_elbow_k(
        k_values=k_values,
        inertias=inertias,
        min_clusters=effective_min,
        fallback_k=4,
    )
    selected_k = max(effective_min, min(int(selected_k), effective_max))
    diagnostics = pd.DataFrame({"k": k_values, "inertia": inertias})

    return selected_k, diagnostics, method


def train_clustering_model(x_scaled: np.ndarray, selected_k: int, random_state: int = 42) -> KMedoids:
    """Train the final KMedoids model with the selected number of clusters."""

    model = create_kmedoids_model(selected_k, random_state=random_state)
    model.fit(x_scaled)
    return model


def choose_cluster_count(x: np.ndarray, max_clusters: int, random_state: int) -> int:
    """Backward-compatible wrapper for inertia-based cluster selection."""

    selected_k, _, _ = select_optimal_k_by_inertia(
        x,
        min_clusters=3,
        max_clusters=max_clusters,
        random_state=random_state,
    )
    return selected_k


def build_cluster_summary(
    data: pd.DataFrame,
    feature_columns: list[str],
    product_columns: list[str],
) -> pd.DataFrame:
    """Build cluster size, numeric medians, product ownership rates, and labels."""

    rows = []
    numeric_features = data[feature_columns].select_dtypes(include=[np.number]).columns.tolist()

    for cluster_id, cluster_df in data.groupby("_cluster"):
        row = {
            "Cluster": int(cluster_id),
            "Nombre de personnes": int(len(cluster_df)),
        }

        for col in numeric_features:
            row[f"Médiane - {col}"] = round(float(pd.to_numeric(cluster_df[col], errors="coerce").median()), 2)

        for product in product_columns:
            row[f"Taux - {product}"] = round(float(cluster_df[product].apply(_binary_value).mean()) * 100, 1)

        row["Libellé automatique"] = make_cluster_label(cluster_df, numeric_features, product_columns)
        rows.append(row)

    return pd.DataFrame(rows).sort_values("Cluster").reset_index(drop=True)


def make_cluster_label(
    cluster_df: pd.DataFrame,
    numeric_features: list[str],
    product_columns: list[str],
) -> str:
    """Create a compact, human-readable cluster label for demos."""

    parts = []
    lower_map = {col.lower(): col for col in numeric_features}

    age_col = next((lower_map[col] for col in lower_map if "âge" in col or "age" in col), None)
    income_col = next((lower_map[col] for col in lower_map if "revenu" in col), None)

    if age_col:
        age = pd.to_numeric(cluster_df[age_col], errors="coerce").median()
        if pd.notna(age):
            if age < 35:
                parts.append("Jeunes")
            elif age < 55:
                parts.append("Actifs établis")
            else:
                parts.append("Seniors")

    if income_col:
        income = pd.to_numeric(cluster_df[income_col], errors="coerce").median()
        if pd.notna(income):
            if income >= 60000:
                parts.append("revenus élevés")
            elif income >= 30000:
                parts.append("revenus moyens")
            else:
                parts.append("revenus modestes")

    product_rates = cluster_df[product_columns].apply(_binary_series).mean().sort_values(ascending=False)
    if not product_rates.empty and product_rates.iloc[0] > 0:
        product_name = product_rates.index[0].replace(PRODUCT_PREFIX, "").strip()
        parts.append(f"appétence {product_name}")

    return " - ".join(parts) if parts else "Segment client"


def _as_single_row(customer: pd.Series | pd.DataFrame) -> pd.DataFrame:
    if isinstance(customer, pd.Series):
        return customer.to_frame().T
    if len(customer) != 1:
        raise ValueError("Une seule ligne client est attendue.")
    return customer.copy()


def _binary_series(series: pd.Series) -> pd.Series:
    return series.apply(_binary_value)


def _binary_value(value: object) -> int:
    if pd.isna(value):
        return 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"oui", "yes", "true", "vrai"}:
            return 1
        try:
            return int(float(normalized) > 0)
        except ValueError:
            return 0
    return int(float(value) > 0)


def _is_owned(value: object) -> bool:
    return _binary_value(value) == 1
