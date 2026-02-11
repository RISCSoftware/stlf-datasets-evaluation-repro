# %%

import pandas as pd

from survey.constants import Paths
from survey.helper import load_classification_map, map_sort_and_rename_classification

label_map, ignore_or_remove = load_classification_map(Paths.manual_classification_map)

library = pd.read_excel(Paths.library_file)

# ensure everything is classified
assert library[library["manual_classification"] == ""].shape[0] == 0

library = library.rename(columns={"Unnamed: 0": "id"}).assign(
    must_read=lambda df: (df["must_read"].replace({"x": True, 1: True, "Michael": "michael"}).fillna(False))
)

for_michael = library[library["must_read"] == "michael"]
for_yvonne = library[library["must_read"] == "yvonne"]

# filter paper for specific people
library = library[library["must_read"].isin([True, False])]

misclassified = [
    # improved classification
    (835, ["pv", "impact"]),
    (800, ["litr"]),
    (3054, ["litr", "impact"]),
    (3752, ["litr", "impact"]),
    (3088, ["litr"]),
    (164, ["p", "mv"]),
    # misclassified as power -> fault and therefore will be removed
    (2712, ["fault"]),
    (4342, ["fault"]),
]

for id, labels in misclassified:
    library.loc[library[library["id"] == id].index, "manual_classification"] = ",".join(labels)

irrelevant_must_reads = [
    (249, False),  # Mislabeled
    (630, False),  # Not interesting for this project
    (763, False),  # manufacturing
    (810, False),
    (899, False),  # restaurant sales
]
for id, labels in irrelevant_must_reads:
    library.loc[library[library["id"] == id].index, "must_read"] = False

# load manual classification
classification = library.set_index("id")["manual_classification"].to_dict()

labels = {k: v.split(",") for k, v in classification.items()}

remove_indices = []
unique_labels = set()
for k, v in labels.items():
    for label in v:
        if label == "":
            # might appear due to splitting errors (extra ',' at the end)
            # already asserted that not a label is missing
            continue

        # do not remove marked papers
        is_must_read = library.loc[library[library["id"] == k].index, "must_read"].iloc[0]
        if label in ignore_or_remove and not is_must_read:
            remove_indices.append(k)
            continue

        unique_labels.add(label.strip())

relevant_unique_labels_map = {element: label_map.get(element, element) for element in unique_labels}

filtered = library[~library["id"].isin(remove_indices)].copy()
# Apply the mapping function to the 'mc' column
filtered["manual_classification"] = filtered["manual_classification"].apply(
    map_sort_and_rename_classification, map_=relevant_unique_labels_map
)

# %%
filtered = filtered.sort_values(by=["must_read", "year", "cites"], ascending=[False, False, False])
# only executed once
# filtered.to_excel(Paths.filtered_library_file, index=False)
# %%
