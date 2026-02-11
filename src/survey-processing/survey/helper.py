# %% [markdown]
# ## Removing Duplicates
# In the next step we want to remove duplicates from the library. To achive this we
# generally add new columns: `marked_for_removal` which is a boolean and a column
# `removal_reason` which is a string.
# - We will first remove duplicates based on the DOI (where a DOI is available). As this is the most secure.
# - We normalize the abstract and authors and title.
#   - Normalization is done by lowercasing, removing punctuation, spaces, and newlines.
# - Removal based upon:
#   - Normalized authors and title in the same year
#   - Normalized authors and abstract in the same year


import string
from pathlib import Path

# %%
# remove duplicates based on DOI
# first compute normalized columns (removing punctioation, spaces, and lowercasing)
import json5 as json
import pandas as pd


def normalize_string_column(data: pd.DataFrame, column: str) -> pd.Series:
    return (
        data[column]
        .astype(str)
        .str.lower()
        .str.strip()
        .str.translate(str.maketrans("", "", string.punctuation))
        .str.translate(str.maketrans("", "", " \n\t\r"))
    )


# %%
# Define a function to map the string values based on the mapping dictionary
def map_sort_and_rename_classification(value, map_: dict[str, str]):
    # Split the string by comma to handle multiple values
    values = value.split(",")
    # Map each value using the mapping dictionary
    mapped_values = [map_.get(v.strip(), v) for v in values]
    # Sort the mapped values
    mapped_values = sorted(mapped_values)
    # Join the mapped values back into a single string
    return ",".join(mapped_values)


def load_classification_map(path: Path):
    with open(path) as f:
        label_map = json.load(f)
        ignore_or_remove = list(label_map["ignore"].keys())

        label_map = label_map
        del label_map["ignore"]
        return label_map, ignore_or_remove
