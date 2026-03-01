import numpy as np
import pandas as pd

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score


class KMeansCluster:

    def __init__(self, min_k=2, max_k=10, random_state=42):
        if min_k < 2:
            raise ValueError("min_k deve ser >= 2.")

        if max_k < min_k:
            raise ValueError("max_k deve ser >= min_k.")

        self.min_k = min_k
        self.max_k = max_k
        self.random_state = random_state

        self.scaler = StandardScaler()
        self.model = None

        self.best_k = None
        self.best_silhouette = None
        self.inertia_values = {}
        self.silhouette_values = {}

    def fit_predict(self, df: pd.DataFrame):

        if df is None or df.empty:
            raise ValueError("DataFrame vazio. Nao e possivel aplicar KMeans.")

        self.inertia_values = {}
        self.silhouette_values = {}
        self.best_k = None
        self.best_silhouette = None
        self.model = None

        X = df.to_numpy(dtype=float)

        if np.isnan(X).any():
            raise ValueError("Existem valores NaN nas features.")

        X_scaled = self.scaler.fit_transform(X)

        self._find_best_k(X_scaled)

        if self.best_k is None:
            raise RuntimeError("Falha ao determinar o melhor K.")

        self.model = KMeans(
            n_clusters=self.best_k,
            random_state=self.random_state,
            n_init=20
        )

        clusters = self.model.fit_predict(X_scaled)

        distances = self._compute_distances(X_scaled, clusters)

        df_result = df.copy()
        df_result["cluster"] = clusters
        df_result["distance_to_centroid"] = distances

        df_result = df_result.sort_values("cluster")

        return (
            df_result,
            self.best_k,
            self.best_silhouette,
            self.inertia_values,
            self.silhouette_values
        )

    def _find_best_k(self, X_scaled):

        n_samples = X_scaled.shape[0]

        max_possible_k = min(self.max_k, n_samples - 1)

        if max_possible_k < self.min_k:
            raise ValueError(
                "Numero insuficiente de amostras para aplicar KMeans "
                f"(minimo necessario: {self.min_k + 1}, recebido: {n_samples})"
            )

        best_score = -1.0
        best_k = None

        for k in range(self.min_k, max_possible_k + 1):

            model = KMeans(
                n_clusters=k,
                random_state=self.random_state,
                n_init=20
            )

            clusters = model.fit_predict(X_scaled)

            # Inertia
            inertia = model.inertia_
            self.inertia_values[k] = inertia

            # Silhouette
            unique_clusters = np.unique(clusters)

            if len(unique_clusters) > 1:
                silhouette = silhouette_score(X_scaled, clusters)
            else:
                silhouette = -1.0

            self.silhouette_values[k] = silhouette

            # Selecao pelo maior Silhouette
            if silhouette > best_score:
                best_score = silhouette
                best_k = k

        self.best_k = best_k
        self.best_silhouette = best_score

    def _compute_distances(self, X_scaled, clusters):

        if self.model is None:
            raise ValueError("Modelo ainda nao treinado.")

        centroids = self.model.cluster_centers_
        distances = np.zeros(len(X_scaled))

        for i, point in enumerate(X_scaled):
            cluster_id = clusters[i]
            centroid = centroids[cluster_id]
            distances[i] = np.linalg.norm(point - centroid)

        return distances

    def get_centroids(self):
        if self.model is None:
            raise ValueError("Modelo ainda nao treinado.")
        return self.model.cluster_centers_

    def inverse_transform_centroids(self):
        if self.model is None:
            raise ValueError("Modelo ainda nao treinado.")

        centroids_scaled = self.model.cluster_centers_
        return self.scaler.inverse_transform(centroids_scaled)