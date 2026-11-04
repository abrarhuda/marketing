"""Download, load, and persist the Hillstrom experiment dataset."""

import json
from pathlib import Path
from typing import Union
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

from .data_validation import clean_dataset

DEFAULT_DATASET_URL = (
    "https://raw.githubusercontent.com/TerraBaseAI/campaign-decisioning-engine/"
    "c44ae9aea5923533ffdaf34522e4937afd813c9e/data/hillstrom.csv"
)
RAW_FILENAME = "hillstrom.csv"
PROCESSED_FILENAME = "hillstrom_validated.csv"
QUALITY_REPORT_FILENAME = "data_quality_report.json"


def load_csv(path: Union[str, Path]) -> pd.DataFrame:
    """Load a CSV file into a DataFrame."""
    source_path = Path(path)
    if not source_path.exists():
        raise FileNotFoundError(f"Dataset not found: {source_path}")
    return pd.read_csv(source_path)


def download_dataset(
    url: str = DEFAULT_DATASET_URL,
    destination: Union[str, Path] = Path("data/raw") / RAW_FILENAME,
    timeout: int = 60,
) -> Path:
    """Download the real dataset to ``destination`` without transforming bytes."""
    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "marketing-ab-data-pipeline/0.1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = response.read()
    except HTTPError as error:
        raise RuntimeError(
            f"Dataset download failed with HTTP {error.code} from {url}. "
            "Check the source URL or download the documented source manually "
            f"to {destination_path}."
        ) from error
    except URLError as error:
        raise RuntimeError(
            f"Dataset download failed for {url}: {error.reason}. "
            "Check network access or download the documented source manually "
            f"to {destination_path}."
        ) from error
    if not payload:
        raise RuntimeError(
            f"Dataset download from {url} returned an empty file. "
            f"Download the source manually to {destination_path}."
        )
    temporary_path = destination_path.with_suffix(destination_path.suffix + ".tmp")
    temporary_path.write_bytes(payload)
    temporary_path.replace(destination_path)
    return destination_path


def run_ingestion_pipeline(
    raw_path: Union[str, Path] = Path("data/raw") / RAW_FILENAME,
    processed_path: Union[str, Path] = Path("data/processed") / PROCESSED_FILENAME,
    quality_report_path: Union[str, Path] = Path("data/processed") / QUALITY_REPORT_FILENAME,
    *,
    download_if_missing: bool = True,
    url: str = DEFAULT_DATASET_URL,
) -> dict[str, object]:
    """Create validated data and a JSON quality report from the raw CSV.

    The raw file is never rewritten. No observations are removed; invalid
    datasets fail validation with an actionable error.
    """
    raw_file = Path(raw_path)
    if not raw_file.exists():
        if not download_if_missing:
            raise FileNotFoundError(f"Dataset not found: {raw_file}")
        download_dataset(url=url, destination=raw_file)
    raw_data = load_csv(raw_file)
    cleaned_data, report = clean_dataset(raw_data)
    processed_file = Path(processed_path)
    processed_file.parent.mkdir(parents=True, exist_ok=True)
    cleaned_data.to_csv(processed_file, index=False)
    report["source_url"] = url
    report["raw_path"] = str(raw_file)
    report["processed_path"] = str(processed_file)
    report_file = Path(quality_report_path)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
