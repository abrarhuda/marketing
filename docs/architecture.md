# Project architecture

The project is organized as a reproducible data-to-analysis pipeline. Raw
source data is never overwritten, analytical transformations are explicit, and
a reserved test set is used for final model evaluation.

```mermaid
flowchart TD
    subgraph Ingestion
        A[MineThatData CSV] --> B[data_ingestion.py]
        B --> C[data_validation.py]
        C --> D[Validated CSV + JSON quality report]
    end

    subgraph Storage
        D --> E[database.py]
        E --> F[(DuckDB)]
        F --> F1[customers]
        F --> F2[experiment_assignments]
        F --> F3[customer_outcomes]
        F1 --> G[customer_experiment_analysis view]
        F2 --> G
        F3 --> G
    end

    subgraph Analysis
        G --> H[SQL EDA]
        G --> I[A/B tests]
        G --> J[Revenue bootstrap]
        G --> K[Predictive ML]
        G --> L[Predictive model evaluation]
    end

    subgraph Outputs
        H --> N[CSV tables]
        I --> O[Statistical results]
        J --> P[Revenue results]
        K --> Q[Model metrics and bundles]
        N --> S[Reports and figures]
        O --> S
        P --> S
        Q --> S
    end
```

## Stage responsibilities

| Stage | Primary implementation | Reproducibility control |
|---|---|---|
| Ingestion | `data_ingestion.py`, `data_validation.py` | Pinned source URL, raw/processed separation, explicit validation failures |
| Database | `database.py`, `sql/01`–`04` | Deterministic schema, primary/foreign keys, join and row-count checks |
| SQL EDA | `eda.py`, `sql/05`–`14` | Queries are versioned and exported as CSV tables |
| A/B testing | `statistical_testing.py` | Fixed definitions, Holm correction, explicit comparison direction |
| Revenue | `revenue_analysis.py`, `sql/15` | Seed `42`, 2,000 customer-level bootstrap iterations, zero spend included |
| Predictive ML | `machine_learning.py` | Seed `42`, stratified 60/20/20 split, preprocessing inside pipelines |
| Visualization | `visualizations.py` | Figures regenerated from saved analysis artifacts |
| Orchestration | `pipeline.py` | One documented command and consistent project-root paths |

## Relational design

The source CSV is normalized into three logical tables:

```text
customers(customer_id PRIMARY KEY, pretreatment attributes...)
experiment_assignments(customer_id PRIMARY KEY, treatment_group,
                        FOREIGN KEY customer_id -> customers)
customer_outcomes(customer_id PRIMARY KEY, visit, conversion, spend,
                  FOREIGN KEY customer_id -> customers)
```

This design makes assignment, customer attributes, and outcomes explicit while
retaining the one-row-per-customer structure of the original experiment. The
analytical view provides a convenient read model for SQL, statistics, and
machine learning.

## Leakage and evaluation boundaries

Pretreatment features are separated from post-assignment outcomes, and only the
former are used for prediction. Models are selected with training and
validation data, then evaluated on the held-out test partition.
