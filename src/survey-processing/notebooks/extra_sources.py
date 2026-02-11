# %%
import numpy as np
import pandas as pd
from pybtex.database import parse_file

from survey.constants import Paths
from survey.helper import (
    load_classification_map,
    map_sort_and_rename_classification,
    normalize_string_column,
)
from survey.typedef import EntryDataFrameSchema, entry_data_frame_order

# %% [markdown]
# # Extra Sources
# While talking to project partner we have been made aware of extra sources
# which might be relevant to our project. We will now include these sources.

# %%

# these are all papers that have been screened so far
total_library = pd.read_excel(Paths.total_library)

# extra source suggested by project partner
csdl = pd.read_excel(Paths.csdl_file)

# %% [markdown]
# ## IEEE CSDL
# The IEEE CSDL is a digital library that contains a large number of papers.
# We will first remove duplicates / any already screened papers and then
# manually classify (same as in normal search) the papers.
# based on this we remove any papers that are not relevant to the project.

# %%

# remove any already screened materials
screened_dois = total_library[~total_library["doi"].isna()]["doi"].tolist()
screened_authors = normalize_string_column(total_library[~total_library["authors"].isna()], "authors")
screened_abstracts = normalize_string_column(total_library[~total_library["abstract"].isna()], "abstract")
screened_titles = normalize_string_column(total_library[~total_library["title"].isna()], "title")

# %%

normalized_authors = normalize_string_column(csdl, "Authors")
normalized_titles = normalize_string_column(csdl, "Title")
normalized_abstract = normalize_string_column(csdl, "Abstract")


# these are manually reviewed and marked as already screened if applicable
manual_rescreen = csdl[(normalized_abstract.isin(screened_abstracts) & normalized_titles.isin(screened_titles))]
manual_rescreening_abstract = csdl[(normalized_abstract.isin(screened_abstracts))]
manual_rescreening_title = csdl[(normalized_titles.isin(screened_titles))]
dois_to_remove = csdl["DOI"][csdl["DOI"].isin(screened_dois)].index

# %%
label_map, ignore_or_remove = load_classification_map(Paths.manual_classification_map)

# %%
# filter manually inserted dupes based on last step
csdl["marked_for_removal"] = False
csdl["removal_reason"] = ""

# handle dupes
duplicates_csdl = ~csdl["dupe_detection"].isna()
csdl.loc[duplicates_csdl, "marked_for_removal"] = True
csdl.loc[csdl[duplicates_csdl].index, "removal_reason"] += "DUP: Duplicate DOI Rescreening"

# filter out rejected papers by definition in dict
rejected = np.zeros(csdl.shape[0]).astype(bool)
for removed_class in ignore_or_remove:
    rejected = rejected | (csdl["manual_classification"].str.split(",").apply(lambda e: removed_class in e))


csdl.loc[csdl[rejected].index, "marked_for_removal"] = True
csdl.loc[csdl[rejected].index, "removal_reason"] += "REJ: Rejected by classification;"

csdl_total_accepted = (~rejected) & (~duplicates_csdl)
unique_rejected_csdl = set(csdl[rejected].index.tolist())
unique_rejected_csdl.update(csdl[duplicates_csdl].index.tolist())
# %%
print(f"Initial CSDL Size: {csdl.shape[0]}")
print(f"Duplicates Removed  : {duplicates_csdl.sum()}")
print(f"Rejected by classification  : {rejected.sum()}")
print(f"Total unique rejected  : {len(unique_rejected_csdl)}")
print(f"Current CSDL Size: {csdl_total_accepted.sum()}")

# %% [markdown]
# ## ACM
# The ACM is another digital library that contains a large number of papers.
# We download the export as `.bib` file and convert it to a dataframe.
# after this we exclude any already screened papers and manually classify
# the rest.


def load_bib_to_dataframe(bib_file_path):
    bib_data = parse_file(bib_file_path)
    entries = []

    for entry in bib_data.entries.values():
        entry_dict = {field: entry.fields.get(field, "") for field in entry.fields}
        entry_dict["ID"] = entry.key
        entries.append(entry_dict)

    return pd.DataFrame(entries)


acm = load_bib_to_dataframe(Paths.acm_bib_file)

# %%
# normalized_authors = normalize_string_column(acm, 'Authors')
normalized_titles = normalize_string_column(acm, "title")
normalized_abstract = normalize_string_column(acm, "abstract")


# these are manually reviewed and marked as already screened if applicable
manual_rescreen = acm[(normalized_abstract.isin(screened_abstracts) & normalized_titles.isin(screened_titles))]
manual_rescreening_abstract = acm[(normalized_abstract.isin(screened_abstracts))]
manual_rescreening_title = acm[(normalized_titles.isin(screened_titles))]

# doi matching (where available)
screened_dois.extend(csdl["DOI"].str.startswith("10.") & (~csdl["DOI"].isna()))
dois_to_remove = acm["ID"][acm["ID"].isin(screened_dois)].index

# %%
acm["manual_classification"] = ""
acm["marked_for_removal"] = False
acm["removal_reason"] = ""

# handle dupes dois
acm.loc[dois_to_remove, "marked_for_removal"] = True
acm.loc[dois_to_remove, "removal_reason"] += "DUP: Duplicated DOI rescreening;"

# %%

# should be only executed once, after manual classification is added just load the ACM file
acm.to_excel(Paths.acm_file_raw, index=False)

# %% [markdown]
# ### Manual Classification
# After the manual classification we will remove any papers
# that are not relevant
# %%
acm = pd.read_excel(Paths.acm_file)
# filter out rejected papers by definition in dict
rejected = np.zeros(acm.shape[0]).astype(bool)
for removed_class in ignore_or_remove:
    rejected = rejected | (
        acm["manual_classification"].astype("str").str.split(",").apply(lambda e: removed_class in e)
    )

# %%
acm_total_accepted = ~(rejected | acm.index.isin(dois_to_remove))
unique_rejected = set(dois_to_remove)
unique_rejected.update(acm[rejected].index.tolist())
# %%
# filtered_csdl.to_excel(Paths.filtered_csdl_file, index=False)
print(f"Initial ACM Size: {acm.shape[0]}")
print(f"Duplicates Removed  : {dois_to_remove.shape[0]}")
print(f"Rejected by classification  : {rejected.sum()}")
print(f"Total unique rejected  : {len(unique_rejected)}")
print(f"Current ACM Size: {acm_total_accepted.sum()}")


# %% [markdown]
# ## Merging and data structure
def determine_document_type_acm(row):
    if pd.notna(row["journal"]):
        return "Journal"
    elif pd.notna(row["booktitle"]):
        return "Conference Proceeding"
    else:
        return "Unknown"


acm_normalized = acm.rename(
    columns={
        "title": EntryDataFrameSchema.title,
        "year": EntryDataFrameSchema.year,
        "doi": EntryDataFrameSchema.doi,
        "url": EntryDataFrameSchema.url,
        "abstract": EntryDataFrameSchema.abstract,
        "publisher": EntryDataFrameSchema.publisher,
        "document_type": EntryDataFrameSchema.document_type,
    }
).assign(
    **{
        EntryDataFrameSchema.within_file_index: lambda x: x.index,
        EntryDataFrameSchema.file_name: "acm.bib",
        EntryDataFrameSchema.source: "ACM",
        EntryDataFrameSchema.document_type: lambda x: x.apply(determine_document_type_acm, axis=1),
        EntryDataFrameSchema.journal_or_conference_name: lambda x: x["journal"].fillna(x["booktitle"]),
        # no authors are given for ACM
        EntryDataFrameSchema.authors: None,
        # cites are not available for this source
        EntryDataFrameSchema.cites: np.nan,
        EntryDataFrameSchema.manual_classification: lambda df: df[EntryDataFrameSchema.manual_classification].apply(
            map_sort_and_rename_classification, map_=label_map
        ),
    }
)[
    entry_data_frame_order
]

final_acm = acm_normalized[acm_total_accepted]
# %%

csdl_normalized = csdl.rename(
    columns={
        "Title": EntryDataFrameSchema.title,
        "Authors": EntryDataFrameSchema.authors,
        "DOI": EntryDataFrameSchema.doi,
        "Abstract": EntryDataFrameSchema.abstract,
        "Category": EntryDataFrameSchema.document_type,
        "Publication": EntryDataFrameSchema.journal_or_conference_name,
    }
).assign(
    **{
        EntryDataFrameSchema.within_file_index: lambda x: x.index,
        EntryDataFrameSchema.file_name: "csdl.xlsx",
        EntryDataFrameSchema.source: "CSDL",
        # No year, url, publisher, or cites information provided
        EntryDataFrameSchema.year: np.nan,
        EntryDataFrameSchema.url: np.nan,
        EntryDataFrameSchema.publisher: np.nan,
        EntryDataFrameSchema.cites: np.nan,
        EntryDataFrameSchema.manual_classification: lambda df: df[EntryDataFrameSchema.manual_classification].apply(
            map_sort_and_rename_classification, map_=label_map
        ),
    }
)[
    entry_data_frame_order
]

final_csdl = csdl_normalized[csdl_total_accepted]
# %%

initial_library = pd.read_excel(Paths.filtered_library_file).assign(
    **{
        EntryDataFrameSchema.journal_or_conference_name: None,
    }
)[entry_data_frame_order]

# %%
initial_screened_library = pd.concat([initial_library, final_acm, final_csdl])
initial_screened_library.to_excel(Paths.initial_screened_library, index=False)

# %%
