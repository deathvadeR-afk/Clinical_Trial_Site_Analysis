"""
Clustering Module for Clinical Trial Site Analysis Platform
Handles embedding-based site clustering using ML techniques
"""

import logging
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import numpy as np

# Set up logging
log_dir = "../logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "clustering.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Try to import scikit-learn
try:
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler

    SKLEARN_AVAILABLE = True
except ImportError:
    logger.warning("Scikit-learn not available. Install with: pip install scikit-learn")
    SKLEARN_AVAILABLE = False
    KMeans = None
    PCA = None
    StandardScaler = None


class SiteClustering:
    """Handles clustering of clinical trial sites based on their characteristics"""

    def __init__(self, db_manager):
        """
        Initialize the site clustering module

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.is_configured = SKLEARN_AVAILABLE

        if not SKLEARN_AVAILABLE:
            logger.warning(
                "Scikit-learn not installed. Clustering functionality will be limited."
            )

    def construct_textual_site_profiles(self) -> List[Dict[str, Any]]:
        """
        Construct textual site profiles for clustering

        Returns:
            List of site profile dictionaries
        """
        try:
            # Get all sites with their metrics
            site_results = self.db_manager.query(
                """
                SELECT sm.*, si.total_studies, si.completed_studies, si.completion_ratio,
                       si.recruitment_efficiency_score, si.experience_index
                FROM sites_master sm
                LEFT JOIN site_metrics si ON sm.site_id = si.site_id
                """
            )

            if not site_results:
                logger.warning("No sites found for clustering")
                return []

            site_profiles = []

            for row in site_results:
                # Create a textual profile for each site
                profile = {
                    "site_id": row["site_id"],
                    "site_name": row["site_name"] or "Unknown Site",
                    "location": f"{row['city'] or ''}, {row['state'] or ''}, {row['country'] or ''}",
                    "institution_type": row["institution_type"] or "Unknown",
                    "accreditation_status": row["accreditation_status"] or "Unknown",
                    "total_studies": row["total_studies"] or 0,
                    "completion_ratio": row["completion_ratio"] or 0,
                    "recruitment_efficiency": row["recruitment_efficiency_score"] or 0,
                    "experience_index": row["experience_index"] or 0,
                    "therapeutic_areas": [],  # Will be populated below
                    "investigator_strength": 0,  # Will be populated below
                }

                # Get therapeutic areas for this site
                therapy_results = self.db_manager.query(
                    "SELECT therapeutic_area FROM site_metrics WHERE site_id = ?",
                    (row["site_id"],),
                )

                if therapy_results:
                    profile["therapeutic_areas"] = [
                        r["therapeutic_area"] for r in therapy_results
                    ]

                # Get investigator metrics
                investigator_results = self.db_manager.query(
                    "SELECT AVG(h_index) as avg_h_index FROM investigators WHERE affiliation_site_id = ?",
                    (row["site_id"],),
                )

                if investigator_results and investigator_results[0]:
                    profile["investigator_strength"] = (
                        investigator_results[0]["avg_h_index"] or 0
                    )

                site_profiles.append(profile)

            logger.info(f"Constructed textual profiles for {len(site_profiles)} sites")
            return site_profiles

        except Exception as e:
            logger.error(f"Error constructing textual site profiles: {e}")
            return []

    def generate_embeddings(
        self, site_profiles: List[Dict[str, Any]]
    ) -> Optional[np.ndarray]:
        """
        Generate embeddings using a simplified approach (in a real implementation,
        this would use Gemini embedding model)

        Args:
            site_profiles: List of site profile dictionaries

        Returns:
            Array of embeddings or None if error occurred
        """
        if not self.is_configured:
            logger.warning("Scikit-learn not available for embedding generation")
            return None

        try:
            # Create feature vectors from site profiles
            feature_vectors = []

            for profile in site_profiles:
                # Extract numerical features
                features = [
                    profile["total_studies"],
                    profile["completion_ratio"],
                    profile["recruitment_efficiency"],
                    profile["experience_index"],
                    profile["investigator_strength"],
                    len(profile["therapeutic_areas"]),  # Number of therapeutic areas
                ]

                feature_vectors.append(features)

            # Convert to numpy array
            embeddings = np.array(feature_vectors, dtype=float)

            logger.info(f"Generated embeddings for {len(embeddings)} sites")
            return embeddings

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return None

    def implement_dimensionality_reduction(
        self, embeddings: np.ndarray
    ) -> Optional[np.ndarray]:
        """
        Implement dimensionality reduction for visualization

        Args:
            embeddings: Array of site embeddings

        Returns:
            Reduced dimensionality embeddings or None if error occurred
        """
        if not self.is_configured or embeddings is None:
            logger.warning("Cannot perform dimensionality reduction")
            return None

        try:
            # Standardize the features
            scaler = StandardScaler()
            standardized_embeddings = scaler.fit_transform(embeddings)

            # Apply PCA to reduce to 2D for visualization
            pca = PCA(n_components=2)
            reduced_embeddings = pca.fit_transform(standardized_embeddings)

            logger.info(f"Reduced embeddings from {embeddings.shape[1]}D to 2D")
            return reduced_embeddings

        except Exception as e:
            logger.error(f"Error in dimensionality reduction: {e}")
            return None

    def apply_clustering_algorithms(
        self, embeddings: np.ndarray, n_clusters: int = 5
    ) -> Optional[List[int]]:
        """
        Apply clustering algorithms to group sites

        Args:
            embeddings: Array of site embeddings
            n_clusters: Number of clusters to create

        Returns:
            List of cluster labels or None if error occurred
        """
        if not self.is_configured:
            logger.warning("Cannot perform clustering - scikit-learn not available")
            return None

        if embeddings is None:
            logger.warning("Cannot perform clustering - embeddings is None")
            return None

        if len(embeddings) == 0:
            logger.warning("Cannot perform clustering - embeddings is empty")
            return None

        try:
            # Ensure we have enough data points for clustering
            if len(embeddings) < n_clusters:
                logger.warning(
                    f"Not enough data points ({len(embeddings)}) for {n_clusters} clusters"
                )
                n_clusters = max(1, len(embeddings))

            # Standardize the features
            scaler = StandardScaler()
            standardized_embeddings = scaler.fit_transform(embeddings)

            # Apply K-Means clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            cluster_labels = kmeans.fit_predict(standardized_embeddings)

            logger.info(f"Applied K-Means clustering with {n_clusters} clusters")
            return cluster_labels.tolist()

        except ValueError as e:
            logger.error(f"Value error in clustering: {e}")
            return None
        except Exception as e:
            logger.error(f"Error in clustering: {e}")
            return None

    def characterize_each_cluster(
        self, site_profiles: List[Dict[str, Any]], cluster_labels: List[int]
    ) -> Dict[int, Dict[str, Any]]:
        """
        Characterize each cluster based on site profiles

        Args:
            site_profiles: List of site profile dictionaries
            cluster_labels: List of cluster labels for each site

        Returns:
            Dictionary with cluster characterizations
        """
        try:
            cluster_characteristics = {}

            # Group sites by cluster
            clusters = {}
            for i, label in enumerate(cluster_labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(site_profiles[i])

            # Characterize each cluster
            for cluster_id, sites in clusters.items():
                # Calculate average metrics for the cluster
                total_studies = np.mean([s["total_studies"] for s in sites])
                completion_ratio = np.mean([s["completion_ratio"] for s in sites])
                recruitment_efficiency = np.mean(
                    [s["recruitment_efficiency"] for s in sites]
                )
                experience_index = np.mean([s["experience_index"] for s in sites])
                investigator_strength = np.mean(
                    [s["investigator_strength"] for s in sites]
                )

                # Find common therapeutic areas
                all_therapies = []
                for site in sites:
                    all_therapies.extend(site["therapeutic_areas"])

                from collections import Counter

                therapy_counts = Counter(all_therapies)
                common_therapies = [
                    therapy for therapy, count in therapy_counts.most_common(3)
                ]

                # Find common institution types
                institution_types = [s["institution_type"] for s in sites]
                institution_counts = Counter(institution_types)
                common_institutions = [
                    inst for inst, count in institution_counts.most_common(2)
                ]

                cluster_characteristics[cluster_id] = {
                    "size": len(sites),
                    "average_total_studies": total_studies,
                    "average_completion_ratio": completion_ratio,
                    "average_recruitment_efficiency": recruitment_efficiency,
                    "average_experience_index": experience_index,
                    "average_investigator_strength": investigator_strength,
                    "common_therapeutic_areas": common_therapies,
                    "common_institution_types": common_institutions,
                    "description": f"Cluster {cluster_id} with {len(sites)} sites",
                }

            logger.info(f"Characterized {len(cluster_characteristics)} clusters")
            return cluster_characteristics

        except Exception as e:
            logger.error(f"Error characterizing clusters: {e}")
            return {}

    def calculate_cluster_quality_metrics(
        self, embeddings: np.ndarray, cluster_labels: List[int]
    ) -> Dict[str, float]:
        """
        Calculate cluster quality metrics

        Args:
            embeddings: Array of site embeddings
            cluster_labels: List of cluster labels for each site

        Returns:
            Dictionary with cluster quality metrics
        """
        if not self.is_configured or embeddings is None:
            logger.warning("Cannot calculate cluster quality metrics")
            return {}

        try:
            from sklearn.metrics import silhouette_score, calinski_harabasz_score

            # Calculate silhouette score
            silhouette = silhouette_score(embeddings, cluster_labels)

            # Calculate Calinski-Harabasz score
            ch_score = calinski_harabasz_score(embeddings, cluster_labels)

            quality_metrics = {
                "silhouette_score": silhouette,
                "calinski_harabasz_score": ch_score,
                "number_of_clusters": len(set(cluster_labels)),
                "total_sites": len(cluster_labels),
            }

            logger.info("Calculated cluster quality metrics")
            return quality_metrics

        except Exception as e:
            logger.error(f"Error calculating cluster quality metrics: {e}")
            return {}

    def use_clustering_insights_for_recommendations(
        self, site_profiles: List[Dict[str, Any]], cluster_labels: List[int]
    ) -> List[Dict[str, Any]]:
        """
        Use clustering insights for recommendations

        Args:
            site_profiles: List of site profile dictionaries
            cluster_labels: List of cluster labels for each site

        Returns:
            List of recommendation dictionaries
        """
        try:
            recommendations = []

            # Group sites by cluster
            clusters = {}
            for i, label in enumerate(cluster_labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(site_profiles[i])

            # Generate recommendations for each cluster
            for cluster_id, sites in clusters.items():
                # Find the best sites in this cluster (based on completion ratio)
                sorted_sites = sorted(
                    sites, key=lambda x: x["completion_ratio"], reverse=True
                )
                top_sites = sorted_sites[:3]  # Top 3 sites

                recommendation = {
                    "cluster_id": cluster_id,
                    "cluster_size": len(sites),
                    "recommended_sites": [
                        {
                            "site_id": site["site_id"],
                            "site_name": site["site_name"],
                            "completion_ratio": site["completion_ratio"],
                            "reason": f"High-performing site in cluster {cluster_id}",
                        }
                        for site in top_sites
                    ],
                    "cluster_strengths": f"Cluster {cluster_id} characteristics",
                    "recommendation_text": f"Consider sites in cluster {cluster_id} for studies requiring similar characteristics",
                }

                recommendations.append(recommendation)

            logger.info(
                f"Generated clustering-based recommendations for {len(recommendations)} clusters"
            )
            return recommendations

        except Exception as e:
            logger.error(f"Error generating clustering recommendations: {e}")
            return []

    def store_clustering_results(
        self,
        site_profiles: List[Dict[str, Any]],
        cluster_labels: List[int],
        cluster_characteristics: Dict[int, Dict[str, Any]],
    ) -> bool:
        """
        Store clustering results in site_clusters table

        Args:
            site_profiles: List of site profile dictionaries
            cluster_labels: List of cluster labels for each site
            cluster_characteristics: Dictionary with cluster characterizations

        Returns:
            True if successful, False otherwise
        """
        try:
            # Process in batches to avoid memory issues with large datasets
            batch_size = 1000
            total_processed = 0
            total_profiles = len(site_profiles)

            for i in range(0, total_profiles, batch_size):
                batch_profiles = site_profiles[i : i + batch_size]
                batch_end = min(i + batch_size, total_profiles)

                logger.info(
                    f"Processing batch {i//batch_size + 1}: sites {i+1} to {batch_end} of {total_profiles}"
                )

                # Insert clustering results for this batch
                batch_data = []
                for j, profile in enumerate(batch_profiles):
                    global_index = i + j
                    if global_index < len(cluster_labels):
                        cluster_id = cluster_labels[global_index]
                        characteristics = cluster_characteristics.get(cluster_id, {})

                        # Prepare data for insertion
                        cluster_data = {
                            "site_id": profile["site_id"],
                            "cluster_label": f"Cluster_{cluster_id}",
                            "cluster_characteristics": json.dumps(characteristics),
                            "distance_to_centroid": 0.0,  # Simplified - would calculate actual distance in real implementation
                            "clustering_algorithm": "KMeans",
                            "clustering_date": datetime.now().isoformat(),
                        }
                        batch_data.append(cluster_data)

                # Insert batch data
                success = self.db_manager.insert_many("site_clusters", batch_data)

                if not success:
                    logger.error(
                        f"Failed to store clustering results for batch {i//batch_size + 1}"
                    )
                    return False

                total_processed += len(batch_data)
                logger.info(
                    f"Successfully processed batch {i//batch_size + 1} ({len(batch_data)} records)"
                )

            logger.info(
                f"Stored clustering results in database ({total_processed} total records)"
            )
            return True

        except Exception as e:
            logger.error(f"Error storing clustering results: {e}")
            return False

    def perform_site_clustering(self, n_clusters: int = 5) -> Dict[str, Any]:
        """
        Main method to perform site clustering

        Args:
            n_clusters: Number of clusters to create

        Returns:
            Dictionary with clustering results
        """
        try:
            if not self.is_configured:
                logger.error("Clustering module not properly configured")
                return {}

            # Step 1: Construct textual site profiles
            logger.info("Step 1: Constructing textual site profiles")
            site_profiles = self.construct_textual_site_profiles()

            if not site_profiles:
                logger.warning("No site profiles constructed")
                return {}

            # Step 2: Generate embeddings
            logger.info("Step 2: Generating embeddings")
            embeddings = self.generate_embeddings(site_profiles)

            if embeddings is None:
                logger.error("Failed to generate embeddings")
                return {}

            # Step 3: Apply dimensionality reduction
            logger.info("Step 3: Applying dimensionality reduction")
            reduced_embeddings = self.implement_dimensionality_reduction(embeddings)

            # Step 4: Apply clustering algorithms
            logger.info("Step 4: Applying clustering algorithms")
            cluster_labels = self.apply_clustering_algorithms(embeddings, n_clusters)

            if cluster_labels is None:
                logger.error("Failed to apply clustering algorithms")
                return {}

            # Step 5: Characterize each cluster
            logger.info("Step 5: Characterizing clusters")
            cluster_characteristics = self.characterize_each_cluster(
                site_profiles, cluster_labels
            )

            # Step 6: Calculate cluster quality metrics
            logger.info("Step 6: Calculating cluster quality metrics")
            quality_metrics = self.calculate_cluster_quality_metrics(
                embeddings, cluster_labels
            )

            # Step 7: Generate recommendations
            logger.info("Step 7: Generating clustering-based recommendations")
            recommendations = self.use_clustering_insights_for_recommendations(
                site_profiles, cluster_labels
            )

            # Step 8: Store results
            logger.info("Step 8: Storing clustering results")
            self.store_clustering_results(
                site_profiles, cluster_labels, cluster_characteristics
            )

            # Prepare results
            results = {
                "site_profiles": site_profiles,
                "cluster_labels": cluster_labels,
                "cluster_characteristics": cluster_characteristics,
                "quality_metrics": quality_metrics,
                "recommendations": recommendations,
                "reduced_embeddings": (
                    reduced_embeddings.tolist()
                    if reduced_embeddings is not None
                    else None
                ),
            }

            logger.info("Site clustering completed successfully")
            return results

        except Exception as e:
            logger.error(f"Error in site clustering: {e}")
            return {}


# Example usage
if __name__ == "__main__":
    print("Site Clustering module ready for use")
    print("This module handles embedding-based site clustering")
