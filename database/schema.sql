-- Database schema for Clinical Trial Site Analysis Platform

-- Core Tables Structure

-- Unique site repository
CREATE TABLE sites_master (
    site_id INTEGER PRIMARY KEY,
    site_name TEXT NOT NULL,
    normalized_name TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    country TEXT,
    latitude REAL,
    longitude REAL,
    institution_type TEXT,
    total_capacity INTEGER,
    accreditation_status TEXT,
    created_at TEXT,
    last_updated TEXT
);

-- Comprehensive trial records
CREATE TABLE clinical_trials (
    nct_id TEXT PRIMARY KEY,
    title TEXT,
    status TEXT,
    phase TEXT,
    study_type TEXT,
    conditions TEXT, -- JSON array
    interventions TEXT, -- JSON array
    enrollment_count INTEGER,
    start_date TEXT,
    completion_date TEXT,
    primary_completion_date TEXT,
    sponsor_name TEXT,
    sponsor_type TEXT,
    last_update_posted TEXT,
    study_first_posted TEXT
);

-- Junction table linking sites to trials
CREATE TABLE site_trial_participation (
    site_trial_id INTEGER PRIMARY KEY,
    site_id INTEGER,
    nct_id TEXT,
    role TEXT,
    recruitment_status TEXT,
    actual_enrollment INTEGER,
    enrollment_start_date TEXT,
    enrollment_end_date TEXT,
    data_submission_quality_score REAL,
    FOREIGN KEY (site_id) REFERENCES sites_master(site_id),
    FOREIGN KEY (nct_id) REFERENCES clinical_trials(nct_id)
);

-- PI and researcher profiles
CREATE TABLE investigators (
    investigator_id INTEGER PRIMARY KEY,
    full_name TEXT,
    normalized_name TEXT,
    affiliation_site_id INTEGER,
    credentials TEXT,
    specialization TEXT,
    total_trials_count INTEGER,
    active_trials_count INTEGER,
    h_index INTEGER,
    total_publications INTEGER,
    recent_publications_count INTEGER,
    FOREIGN KEY (affiliation_site_id) REFERENCES sites_master(site_id)
);

-- Research output tracking
CREATE TABLE pubmed_publications (
    publication_id INTEGER PRIMARY KEY,
    pmid TEXT,
    title TEXT,
    authors TEXT, -- JSON array
    journal TEXT,
    publication_date TEXT,
    citations_count INTEGER,
    abstract TEXT,
    keywords TEXT, -- JSON array
    mesh_terms TEXT, -- JSON array
    investigator_id INTEGER,
    site_id INTEGER,
    FOREIGN KEY (investigator_id) REFERENCES investigators(investigator_id),
    FOREIGN KEY (site_id) REFERENCES sites_master(site_id)
);

-- Pre-calculated performance indicators
CREATE TABLE site_metrics (
    metric_id INTEGER PRIMARY KEY,
    site_id INTEGER,
    therapeutic_area TEXT,
    total_studies INTEGER,
    completed_studies INTEGER,
    terminated_studies INTEGER,
    withdrawn_studies INTEGER,
    avg_enrollment_duration_days REAL,
    completion_ratio REAL,
    recruitment_efficiency_score REAL,
    experience_index REAL,
    last_calculated TEXT,
    FOREIGN KEY (site_id) REFERENCES sites_master(site_id)
);

-- Granular quality assessment
CREATE TABLE data_quality_scores (
    quality_id INTEGER PRIMARY KEY,
    site_id INTEGER,
    nct_id TEXT,
    completeness_score REAL,
    recency_score REAL,
    consistency_score REAL,
    overall_quality_score REAL,
    missing_fields TEXT, -- JSON array
    last_update_lag_days INTEGER,
    calculation_date TEXT,
    FOREIGN KEY (site_id) REFERENCES sites_master(site_id),
    FOREIGN KEY (nct_id) REFERENCES clinical_trials(nct_id)
);

-- Pre-computed compatibility rankings
CREATE TABLE match_scores (
    match_id INTEGER PRIMARY KEY,
    site_id INTEGER,
    target_therapeutic_area TEXT,
    target_phase TEXT,
    target_intervention_type TEXT,
    therapeutic_match_score REAL,
    phase_match_score REAL,
    intervention_match_score REAL,
    geographic_match_score REAL,
    overall_match_score REAL,
    calculated_at TEXT,
    FOREIGN KEY (site_id) REFERENCES sites_master(site_id)
);

-- LLM-generated summaries
CREATE TABLE ai_insights (
    insight_id INTEGER PRIMARY KEY,
    site_id INTEGER,
    strengths_summary TEXT,
    weaknesses_summary TEXT,
    recommendation_text TEXT,
    confidence_score REAL,
    gemini_model_version TEXT,
    generated_at TEXT,
    FOREIGN KEY (site_id) REFERENCES sites_master(site_id)
);

-- ML grouping results
CREATE TABLE site_clusters (
    cluster_id INTEGER PRIMARY KEY,
    site_id INTEGER,
    cluster_label TEXT,
    cluster_characteristics TEXT, -- JSON
    distance_to_centroid REAL,
    clustering_algorithm TEXT,
    clustering_date TEXT,
    FOREIGN KEY (site_id) REFERENCES sites_master(site_id)
);

-- Indexing Strategy
CREATE INDEX idx_sites_therapeutic_area ON site_metrics(site_id, therapeutic_area);
CREATE INDEX idx_trials_status ON clinical_trials(nct_id, status);
CREATE INDEX idx_sites_completion_ratio ON site_metrics(site_id, completion_ratio);
CREATE INDEX idx_therapeutic_area_only ON site_metrics(therapeutic_area);
CREATE INDEX idx_investigator_h_index ON investigators(investigator_id, h_index);
CREATE INDEX idx_site_name_fts ON sites_master(site_name);
CREATE INDEX idx_investigator_name_fts ON investigators(full_name);