# %%
import glob
import json
import os
import re
from pathlib import Path

import pandas as pd

from survey.constants import Paths
from survey.helper import normalize_string_column
from survey.typedef import EntryDataFrameSchema

# %% [markdown]
# ## Imports
# We will import the exports from the different sources and unify them into a single DataFrame.
# For this we always gather all files and select columns based on the schema.
# We also try to impute missing values (e.g. for the number of citations) and normalize the data.


# %%
def try_extract_doi_scholar(data: dict) -> str:
    """
    Tries to extract the DOI from a given dictionary containing scholarly article information.

    The method first checks if the 'doi' field is present and valid. If not, it attempts to extract
    the DOI from the 'article_url' and 'fulltext_url' fields using a regular expression.

    Args:
        data (dict): A dictionary containing scholarly article information. Expected keys include
                     'doi', 'article_url', and 'fulltext_url'.

    Returns:
        str: The extracted DOI if found, otherwise None.
    """
    # Check if the 'doi' field is present and valid
    if "doi" in data and data["doi"]:
        return data["doi"]

    # Define a function to extract DOI from a URL
    def extract_doi_from_url(url: str) -> str:
        # Use a regular expression to extract the DOI from the URL
        match = re.search(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", url, re.IGNORECASE)
        if match:
            return match.group(0)
        return None

    # Try to extract DOI from 'article_url'
    if "article_url" in data:
        doi = extract_doi_from_url(data["article_url"])
        if doi:
            return doi

    # Try to extract DOI from 'fulltext_url'
    if "fulltext_url" in data:
        doi = extract_doi_from_url(data["fulltext_url"])
        if doi:
            return doi

    # Return None if DOI is not found
    return None


def unify_ieee_xplore_exports(data_dir: Path):
    records = []
    ieee_files = glob.glob(os.path.join(data_dir, "ieee*.csv"))

    # Process each file
    for file_path in ieee_files:
        export_raw = pd.read_csv(file_path)
        export_normalized = (
            export_raw[
                [
                    "Document Title",
                    "DOI",
                    "Document Identifier",
                    "Authors",
                    "Publisher",
                    "Publication Year",
                    "Abstract",
                    "PDF Link",
                    "Article Citation Count",
                ]
            ]
            .rename(
                columns={
                    "Document Title": EntryDataFrameSchema.title,
                    "Authors": EntryDataFrameSchema.authors,
                    "Publication Year": EntryDataFrameSchema.year,
                    "DOI": EntryDataFrameSchema.doi,
                    "PDF Link": EntryDataFrameSchema.url,
                    "Abstract": EntryDataFrameSchema.abstract,
                    "Publisher": EntryDataFrameSchema.publisher,
                    "Article Citation Count": EntryDataFrameSchema.cites,
                    "Document Identifier": EntryDataFrameSchema.document_type,
                }
            )
            .assign(
                within_file_index=lambda x: x.index,
                file_name=os.path.basename(file_path),
                source="IEEE Xplore",
            )
        )

        # manually checked all missings cites, only one paper has cites
        export_normalized.loc[26, EntryDataFrameSchema.cites] = 6

        # all others have 0
        export_normalized[EntryDataFrameSchema.cites] = (
            export_normalized[EntryDataFrameSchema.cites].fillna(0).astype(int)
        )

        records.extend(export_normalized.to_dict(orient="records"))
    return records


def unify_scopus_exports(data_dir: Path):
    records = []
    scopus_files = glob.glob(os.path.join(data_dir, "scopus*.csv"))

    # Process each file
    for file_path in scopus_files:
        export_raw = pd.read_csv(file_path)
        export_normalized = (
            export_raw[
                [
                    "Title",
                    "DOI",
                    "Authors",
                    "Publisher",
                    "Year",
                    "Cited by",
                    "Abstract",
                    "Document Type",
                    "Link",
                ]
            ]
            .rename(
                columns={
                    "Title": EntryDataFrameSchema.title,
                    "Authors": EntryDataFrameSchema.authors,
                    "Year": EntryDataFrameSchema.year,
                    "DOI": EntryDataFrameSchema.doi,
                    "Link": EntryDataFrameSchema.url,
                    "Abstract": EntryDataFrameSchema.abstract,
                    "Publisher": EntryDataFrameSchema.publisher,
                    "Cited by": EntryDataFrameSchema.cites,
                    "Document Type": EntryDataFrameSchema.document_type,
                }
            )
            .assign(
                within_file_index=lambda x: x.index,
                file_name=os.path.basename(file_path),
                source="Scopus",
            )
        )
        records.extend(export_normalized.to_dict(orient="records"))
    return records


def unify_scholar_exports(data_dir: Path):
    records = []
    scholar_files = glob.glob(os.path.join(data_dir, "results_scholar_*.json"))

    # Process each file
    for file_path in scholar_files:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
            for record in data:
                export_normalized = {
                    # manually set
                    EntryDataFrameSchema.within_file_index: data.index(record),
                    EntryDataFrameSchema.file_name: os.path.basename(file_path),
                    EntryDataFrameSchema.source: "Scholar",
                    # extract from scholar specific
                    EntryDataFrameSchema.title: record.get("title"),
                    EntryDataFrameSchema.authors: ", ".join(record.get("authors", [])),
                    EntryDataFrameSchema.year: record.get("year"),
                    EntryDataFrameSchema.doi: try_extract_doi_scholar(
                        record
                    ),  # DOI is not present in the JSON structure
                    EntryDataFrameSchema.url: record.get("fulltext_url") or record.get("article_url"),
                    EntryDataFrameSchema.abstract: record.get("abstract"),
                    EntryDataFrameSchema.publisher: record.get("publisher"),
                    EntryDataFrameSchema.cites: record.get("cites"),
                }
                records.append(export_normalized)
    return records


def unify_manual_search(data_dir: Path):
    records = []
    json_files = glob.glob(str(data_dir / "manual_searches*.json"))
    for file_path in json_files:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for index, record in enumerate(data):
                parsed_record = {
                    EntryDataFrameSchema.within_file_index: index,
                    EntryDataFrameSchema.file_name: os.path.basename(file_path),
                    EntryDataFrameSchema.source: "Manual Search",
                    EntryDataFrameSchema.title: record.get("title"),
                    EntryDataFrameSchema.authors: ", ".join(record.get("author", [])),
                    EntryDataFrameSchema.year: record.get("year"),
                    EntryDataFrameSchema.doi: record.get(
                        "DOI", record.get("url")
                    ),  # Use DOI if present, otherwise use URL
                    EntryDataFrameSchema.url: record.get("url"),
                    EntryDataFrameSchema.abstract: record.get("abstract"),
                    EntryDataFrameSchema.publisher: record.get("publisher"),
                    EntryDataFrameSchema.document_type: "Conference Paper",  # Assume all records are conference papers
                    EntryDataFrameSchema.cites: record.get("cites"),
                }
                records.append(parsed_record)
    return records


# %%
rows = []
rows.extend(unify_ieee_xplore_exports(Paths.data_dir))
rows.extend(unify_scopus_exports(Paths.data_dir))
rows.extend(unify_scholar_exports(Paths.data_dir))
rows.extend(unify_manual_search(Paths.data_dir))

# %% [markdown]
# ## Normalization
# At this point we have a library full of articles from different sources.
# We will now normalize the data and remove duplicates.

# %%
unified_library = pd.DataFrame.from_records(rows)
initial_screening_size = unified_library.shape[0]

# %%
# strip https://doi.org/ from doi
unified_library[EntryDataFrameSchema.doi] = unified_library[EntryDataFrameSchema.doi].str.replace(
    "https://doi.org/", ""
)

unified_library["normalized_abstract"] = normalize_string_column(unified_library, "abstract")
unified_library["normalized_authors"] = normalize_string_column(unified_library, "authors")
unified_library["normalized_title"] = normalize_string_column(unified_library, "title")

unified_library["marked_for_removal"] = False
unified_library["removal_reason"] = ""

# %%
# calculate a mask which marks all duplicated DOIs, dois should be identifier
mask_duplicate_doi = (~unified_library[EntryDataFrameSchema.doi].isna()) & (
    unified_library[EntryDataFrameSchema.doi].duplicated()
)

# mark the rows for removal and append the removal reason using the mask
unified_library.loc[mask_duplicate_doi, "marked_for_removal"] = True
unified_library.loc[mask_duplicate_doi, "removal_reason"] += "DUP: Duplicated DOI detected"

# %%
# we assume that a given list of authors publishes only a paper with
# the same name in the same year
duplicate_indices_per_authors_title_year = (
    unified_library.groupby("normalized_authors")
    # get indices of all dupes per author. Do not mark the first occurance
    # After this we get a pd.Series which looks like this:
    # normalized_authors
    # aaabdullahamahmedtrashidhveisi                              [3607]
    # aaahmedssayedaabdoulhaliksmoutari               [1450, 2179, 3870]
    .apply(
        lambda group: group[group.duplicated(["normalized_title", "year"], keep="first")].index.tolist(),
        include_groups=False,
    )
    # explode the list in the series to receive a normalized dataframe
    .explode()
    # drop any NA from the series and ensure the indices are integers
    .dropna()
    .astype(int)
    .tolist()
)

unified_library.loc[duplicate_indices_per_authors_title_year, "marked_for_removal"] = True
unified_library.loc[
    duplicate_indices_per_authors_title_year, "removal_reason"
] += "DUP: Same authors and title in the same year;"

# %%
duplicate_indices_per_author_abstract_year = (
    unified_library.groupby("normalized_authors")
    # get indices of all dupes per author. Do not mark the first occurance
    # After this we get a pd.Series which looks like this:
    # normalized_authors
    # aaabdullahamahmedtrashidhveisi                              [3607]
    # aaahmedssayedaabdoulhaliksmoutari               [1450, 2179, 3870]
    .apply(
        lambda group: group[group.duplicated(["normalized_abstract", "year"], keep=False)].index.tolist(),
        include_groups=False,
    )
    # explode the list in the series to receive a normalized dataframe
    .explode()
    # drop any NA from the series and ensure the indices are integers
    .dropna()
    .astype(int)
    .tolist()
)

unified_library.loc[duplicate_indices_per_author_abstract_year, "marked_for_removal"] = True
unified_library.loc[
    duplicate_indices_per_author_abstract_year, "removal_reason"
] += "DUP: Same authors and abstract in the same year;"

# %% [markdown]
# ## Manually Removing Duplicates
# We will now manually remove duplicates based the following masks

# %%
mask_duplicate_abstract = (
    # check for NAs in the not normalized abstract to avoid issues with converted NAs
    (~unified_library["abstract"].isna())
    & unified_library["normalized_abstract"].duplicated(keep=False)
)

mask_duplicate_title = (~unified_library["title"].isna()) & unified_library["title"].duplicated(keep=False)

# %%
# manually look at the rest of the duplicates
# based on mask_duplicated_title
duplicates_indices_manual_mask_duplicate_title = [
    26,
    757,
    574,
    665,
    1245,
    935,
    457,
    644,
    734,
    2560,
    1845,
    754,
    5114,
    827,
    4316,
    4327,
]
unified_library.loc[duplicates_indices_manual_mask_duplicate_title, "marked_for_removal"] = True
unified_library.loc[
    duplicates_indices_manual_mask_duplicate_title, "removal_reason"
] += "DUP: Manually selected (mask_duplicated_title);"

# %%
duplicates_indices_manual_mask_duplicate_abstract = [1976, 4308, 4412, 1244, 1195, 1066]
unified_library.loc[duplicates_indices_manual_mask_duplicate_abstract, "marked_for_removal"] = True
unified_library.loc[
    duplicates_indices_manual_mask_duplicate_abstract, "removal_reason"
] += "DUP: Manually selected (mask_duplicated_abstract);"

# %% [markdown]
# ### Cleanup
# We will now remove caluclated columns and any duplicates from the library.

# %%
unified_library = unified_library.drop(columns=["normalized_abstract", "normalized_authors", "normalized_title"])
# only executed once
# unified_library.to_excel(Paths.total_library, index=False)
unified_library = unified_library[~unified_library["marked_for_removal"]]

# %%
removed_duplicates = initial_screening_size - unified_library.shape[0]
print(f"Initial Library Size: {initial_screening_size}")
print(f"Duplicates Removed  : {removed_duplicates}")
print(f"Current Library Size: {unified_library.shape[0]}")
unified_library = unified_library.drop(columns=["marked_for_removal", "removal_reason"])

# %%
# only executed once
# unified_library.to_excel(Paths.library_file, index=True)

# %%
