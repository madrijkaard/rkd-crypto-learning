import os
import traceback

from config import (
    SYMBOLS,
    BASE_SYMBOL,
    TIMEFRAME,
    CANDLE_LIMIT,
    MIN_K,
    MAX_K,
    RANDOM_STATE,
    SAVE_RESULTS,
    OUTPUT_FILE,
    SAVE_REPORT,
    REPORT_FILE,
)

from data.data_fetcher import DataFetcher
from features.feature_engineer import FeatureEngineer
from clustering.kmeans_cluster import KMeansCluster
from visualization.cluster_visualizer import ClusterVisualizer


def main():
    print("=" * 60)
    print(" INICIANDO PIPELINE DE CLUSTERIZAÇÃO CRIPTO")
    print("=" * 60)

    try:
        print("\n Baixando dados da Binance...")
        data_fetcher = DataFetcher()

        market_data = data_fetcher.fetch_multiple(
            symbols=SYMBOLS,
            timeframe=TIMEFRAME,
            limit=CANDLE_LIMIT,
        )

        print(" Dados carregados com sucesso.")

        print("\n Gerando features quantitativas...")
        feature_engineer = FeatureEngineer(base_symbol=BASE_SYMBOL)

        features_df = feature_engineer.build_feature_matrix(market_data)

        print("\n Features geradas:")
        print(features_df)

        print("\n Executando K-Means com seleção automática de K...")

        kmeans_cluster = KMeansCluster(
            min_k=MIN_K,
            max_k=MAX_K,
            random_state=RANDOM_STATE,
        )

        (
            clustered_df,
            best_k,
            best_silhouette,
            inertia_vals,
            silhouette_vals,
        ) = kmeans_cluster.fit_predict(features_df)

        print("\n Resultado da Clusterização:")
        print(clustered_df[["cluster"]])

        print("\n Melhor número de clusters encontrado:", best_k)
        print(f" Melhor Silhouette Score: {best_silhouette:.4f}")

        print("\n Inertia por K:")
        for k, inertia in inertia_vals.items():
            print(f" K={k} → Inertia={inertia:.4f}")

        print("\n Silhouette por K:")
        for k, score in silhouette_vals.items():
            print(f" K={k} → Silhouette={score:.4f}")

        os.makedirs("out", exist_ok=True)

        if SAVE_RESULTS:
            output_df = clustered_df.reset_index()
            output_df.to_csv(OUTPUT_FILE, index=False)
            print(f"\n Resultado salvo em: {OUTPUT_FILE}")

        if SAVE_REPORT:
            print("\n Gerando relatório visual...")
            visualizer = ClusterVisualizer(output_file=REPORT_FILE)
            visualizer.generate(
                clustered_df=clustered_df,
                best_k=best_k,
                best_silhouette=best_silhouette,
                silhouette_vals=silhouette_vals,
                inertia_vals=inertia_vals,
            )

        print("\n Pipeline finalizado com sucesso.")
        print("=" * 60)

    except Exception as e:
        print("\n ERRO DURANTE EXECUÇÃO:")
        print(str(e))
        traceback.print_exc()


if __name__ == "__main__":
    main()