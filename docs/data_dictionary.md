# Hillstrom experiment data dictionary

This dictionary describes the source fields and the derived identifiers used by
the project. The source does not contain a customer identifier; `customer_id`
is a stable one-based surrogate generated from row position during ingestion.

## Source fields

| Field | Type after validation | Role | Description |
|---|---|---|---|
| `recency` | Integer | Pretreatment feature | Number of months since the customer's last purchase. Nonnegative. |
| `history_segment` | Categorical string | Pretreatment feature | Source-defined historical purchase-value segment. Labels are preserved. |
| `history` | Numeric | Pretreatment feature | Historical customer spending before the experiment. Nonnegative. |
| `mens` | Integer/binary indicator | Pretreatment feature | Historical indicator associated with mens merchandise. |
| `womens` | Integer/binary indicator | Pretreatment feature | Historical indicator associated with womens merchandise. |
| `zip_code` | Categorical string | Pretreatment feature | Source geographic classification. The source typo `Surburban`, where present, is preserved. |
| `newbie` | Integer/binary indicator | Pretreatment feature | Indicates whether the customer is new or returning according to the source. |
| `channel` | Categorical string | Pretreatment feature | Historical purchase channel. |
| `segment` | Categorical string | Randomized assignment | One of `No E-Mail`, `Mens E-Mail`, or `Womens E-Mail`. This is the treatment assignment and is not recoded. |
| `visit` | Integer/binary outcome | Primary outcome | Whether the customer visited the website after assignment: `0` or `1`. |
| `conversion` | Integer/binary outcome | Secondary outcome | Whether the customer made a purchase after assignment: `0` or `1`. |
| `spend` | Numeric | Secondary outcome | Post-assignment customer spend. Includes zero for nonpurchasers and must be nonnegative. |

## Derived and relational fields

| Field | Location | Type | Description |
|---|---|---|---|
| `customer_id` | Validated CSV and all DuckDB tables | Integer | Stable one-based row-position surrogate. It is not an original customer ID. |
| `treatment_group` | `experiment_assignments`, analytical view | Categorical string | Clear analytical name for the source `segment` assignment. |

## Modeling boundaries

The predictive models use only:

```text
recency
history
history_segment
mens
womens
zip_code
newbie
channel
```

They exclude `treatment_group`, `visit`, `conversion`, and `spend` from the
feature matrix. Treatment assignment is used only to stratify partitions and
is retained for experiment analysis, not used as a predictive feature.

## Validation rules

The ingestion pipeline:

- requires every source field listed above;
- normalizes column names to lowercase underscore-separated names;
- parses numeric fields and preserves source category labels;
- rejects missing required values;
- requires all three expected assignment groups;
- requires binary `visit` and `conversion`;
- rejects negative `recency`, `history`, or `spend`;
- reports exact duplicate rows without removing them; and
- preserves the raw downloaded file unchanged.
