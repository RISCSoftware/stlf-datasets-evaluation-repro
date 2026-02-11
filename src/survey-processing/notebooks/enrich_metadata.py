# possibilities
# year
# authors
# what if doi missing?
# document type (Journal, Conference Proceeding, ...)
# journal or conference name

# %%
# get by doi

import json
from collections import defaultdict

import numpy as np
import pandas as pd
import requests

from survey.constants import Paths
from survey.typedef import EntryDataFrameSchema as schema


def query_crossref_by_doi(doi: str):
    url = f"https://api.crossref.org/works/{doi}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


# %%
initial_screened_library = pd.read_excel(Paths.initial_screened_library)
records = initial_screened_library.to_dict(orient="records")

# %%
crossrefs = {}
for record in records:
    doi = record.get(schema.doi)
    if doi and doi != np.nan:
        try:
            crossref_data = query_crossref_by_doi(doi)
            crossrefs[doi] = crossref_data["message"]
        except requests.HTTPError as e:
            print(f"Failed to retrieve data for DOI {doi}: {e}")

replacement_counts = defaultdict(int)


def enrich_record(record, schema, crossref_data):
    enriched_record = record.copy()

    # define the fields to check and their corresponding keys in crossref_data
    fields = {
        schema.publisher: "publisher",
        schema.url: "URL",
        schema.cites: "is-referenced-by-count",
        schema.document_type: "type",
        schema.journal_or_conference_name: "container-title",
    }

    # iterate over the fields and check for replacements
    for field, crossref_key in fields.items():
        if not isinstance(record.get(field), str) and crossref_data.get(crossref_key):
            enriched_record[field] = crossref_data.get(crossref_key)
            replacement_counts[field] += 1

    # always replace the abstract
    enrich_record[schema.abstract] = crossref_data.get("abstract") or enrich_record.get(schema.abstract)

    return enriched_record


# %%
enriched = []
for record in records:
    enriched_record = record.copy()
    doi = record.get(schema.doi)
    if doi and not pd.isna(doi) and crossrefs.get(doi):
        enriched_record = enrich_record(record, schema, crossrefs[doi])
    enriched.append(enriched_record)

# %%


def compare_missingness_per_column(before_df: pd.DataFrame, after_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compare the missingness before and after an enrich step for each column.

    Args:
        before_df (pd.DataFrame): DataFrame before the enrich step.
        after_df (pd.DataFrame): DataFrame after the enrich step.

    Returns:
        pd.DataFrame: DataFrame showing the missingness before and after the enrich step for each column.
    """
    # Calculate the percentage of missing values for each column in the before DataFrame
    before_missingness = before_df.isnull().mean() * 100

    # Calculate the percentage of missing values for each column in the after DataFrame
    after_missingness = after_df.isnull().mean() * 100

    # Create a DataFrame to compare the missingness
    comparison_df = pd.DataFrame(
        {
            "Column": before_df.columns,
            "Before Enrich (%)": before_missingness,
            "After Enrich (%)": after_missingness,
            "Difference (%)": before_missingness - after_missingness,
        }
    ).reset_index(drop=True)

    return comparison_df


# %%
enriched_library = pd.DataFrame.from_records(enriched)
missigness = compare_missingness_per_column(initial_screened_library, enriched_library)
print(missigness.to_markdown())

# %%
manual_urls = {
    489: "https://doi.org/10.1109/ICEI57064.2022.00035",
    492: "https://doi.org/10.1109/STI56238.2022.10103285",
    493: "https://arxiv.org/pdf/2110.11466",
    497: "https://doi.org/10.1109/MLISE54096.2021.00018",
    498: "https://doi.org/10.1109/MICRO56248.2022.00082",
    504: "https://doi.org/10.48550/arXiv.2004.14690",
    505: "https://doi.org/10.48550/arXiv.1911.02549",
}
for id, url in manual_urls.items():
    enriched_library.loc[enriched_library.index == id, schema.url] = url

# %%

article_is_findable = enriched_library[schema.doi].isna() & enriched_library[schema.url].isna()

assert article_is_findable.sum() == 0, "Some articles are not findable by DOI or URL"

# %%
enriched_library.to_excel(Paths.enriched_library)

# %%
with open(Paths.data_dir / "crossrefs.json", "w") as f:
    json.dump(crossrefs, f)

# %%
