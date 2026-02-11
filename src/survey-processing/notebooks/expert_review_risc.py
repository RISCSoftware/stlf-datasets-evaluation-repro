# %%
import os
import re
from typing import Callable, Dict, List

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

from survey.constants import ExpertReviewsRISC

# %%
# Check if each file used in this notebook actually exists
required_files = [
    ExpertReviewsRISC.foberhau,
    ExpertReviewsRISC.febner,
    ExpertReviewsRISC.skritzin,
]

for file_path in required_files:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Script depends upon the file '{file_path}' which does not exist.")


# %%
def display_barchart(
    values: pd.Series,
    order: List[str] = None,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
):
    """Display a bar chart for the given values."""
    plt.figure(figsize=(10, 6))
    sns.countplot(x=values, order=order)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=45)  # Tilt the x labels by 45 degrees
    plt.show()


# %% [markdown]
# ## Expert reviews RISC
# First, we take a look individually at the reviews of the experts.
# ### Felix Oberhauser
# We start with Felix Oberhauser. He ranked the papers by relevance.
# 1 = very relevant, 2 = relevant, 3 = not very relevant, 4 = irrelevant, 5 = very irrelevant.
# A paper marked with the letter 'd' might be relevant but are very generic (e.g. not related to the load prediction).

# %%
review_foberhau = pd.read_excel(ExpertReviewsRISC.foberhau)
ranking_foberhau = review_foberhau["FOBERHAU"].astype(str)
# map the value 'd' to 'generic'
ranking_foberhau = ranking_foberhau.apply(lambda x: "generic" if x == "d" else x)
display_barchart(
    ranking_foberhau,
    order=["1", "2", "3", "4", "5", "generic"],
    title="Felix Oberhauser - Ranking",
    xlabel="Category",
    ylabel="Count",
)

# %% [markdown]
# The figure shows we have a small number of very relevant papers.
# Most papers are rated as relevant or neutral. In his own words, he does not consider
# 4 or 5 as relevant and while the generic papers might be interesting they are not the focus of the review.

# %% [markdown]
# ### Franz Ebner
# Franz Ebner classified the papers into categories. The categories are unified according to his specification (see dict later on).


def preprocess_febner(series: pd.Series) -> pd.Series:
    """Preprocess Franz Ebner's categories."""

    def map_category(category):
        if pd.isna(category):
            return "No Opinion"
        if "Irrelevant" in category:
            return "Irrelevant"
        elif "Relevant" in category:
            return category  # Keep the specific category if it's marked as 'Relevant'
        elif "IDK" in category:
            return "No Opinion"
        else:
            return category

    return series.apply(map_category)


review_febner = pd.read_excel(ExpertReviewsRISC.febner)
ranking_febner = preprocess_febner(review_febner["FEBNER"].dropna())
top_n_categories = ranking_febner.value_counts().head(10).index
filtered_ranking_febner = ranking_febner[ranking_febner.isin(top_n_categories)]

display_barchart(
    filtered_ranking_febner,
    order=top_n_categories,
    title="Franz Ebner - Categories",
    xlabel="Category",
    ylabel="Count",
)

# %% [markdown]
# The figure shows the top 10 categories Franz Ebner classified the papers into. It seems that many papers were marked as relevant.
# Many seem to focus not explicitly on demand prediction but rather on exogenous factors and are often marked as irrelevant.
# Additionally, the reviewer marked some papers as 'IDK' (I don't know).

# %% [markdown]
# ### Stefanie Kritzinger-Griebler
# Finished the review and seemed rather strict in her ratings. She rated the papers from 1 to 5.

review_skritzin = pd.read_excel(ExpertReviewsRISC.skritzin)
ranking_skritzin = review_skritzin["SKRITZIN"].astype(str)
display_barchart(
    ranking_skritzin,
    order=["1", "2", "3", "4", "5"],
    title="Stefanie Kritzinger-Griebler - Ranking",
    xlabel="Category",
    ylabel="Count",
)

# %% [markdown]
# ## Summary

# %%
# Filter relevant and irrelevant papers based on Franz Ebner's rankings
relevant_indices = ranking_febner[ranking_febner.str.contains("Relevant")].index
relevant_foberhau = ranking_foberhau.loc[relevant_indices]
display_barchart(
    relevant_foberhau,
    order=["1", "2", "3", "4", "5", "generic"],
    title="Felix Oberhauser - Rankings of Papers Marked as Relevant by Franz Ebner",
    xlabel="Category",
    ylabel="Count",
)

irrelevant_indices = ranking_febner[ranking_febner.str.contains("Irrelevant")].index
irrelevant_foberhau = ranking_foberhau.loc[irrelevant_indices]
display_barchart(
    irrelevant_foberhau,
    order=["1", "2", "3", "4", "5", "generic"],
    title="Felix Oberhauser - Rankings of Papers Marked as Irrelevant by Franz Ebner",
    xlabel="Category",
    ylabel="Count",
)

# %% [markdown]
# ## Agreement between experts
# We calculate the agreement between experts by comparing the categories they assigned
# to the papers. To accomplish this, we define synonyms (meaning these fall in the same category),
# and look at how much agreement there is between the experts.
#
# ### Example
# In the following example, we have three experts who have rated a set of papers.
# We define synonyms for each expert to account for variations in their terminology.
#
# ```python
# data = {
#     "Expert1": ["Relevant", "Irrelevant, Wind", "Relevant, Generic", "IDK", "Irrelevant"],
#     "Expert2": ["Relevant", "Rekevant", "Relevant", "IDK", "Irrelevant, Solar"],
#     "Expert3": ["Relevant", "Irrelevant", "Relevant, Demand Side", "IDK", "Irrelevant, Generic"],
# }
# expert_rankings = pd.DataFrame(data)
#
# synonyms = {"Expert1": ["relevant"], "Expert2": ["Relevant", "Rekevant"], "Expert3": ["Relevant, Demand Side"]}
#
# def find_category(
#     series: pd.Series,
#     synonyms: List[str],
#     comparison: Callable[[str, str], bool] = lambda expert_opinion, synonym: expert_opinion.lower() == synonym.lower(),
# ) -> pd.Series:
#     """Replace synonyms with the unique value and create a boolean series."""
#     return series.apply(lambda x: any(comparison(x, synonym) for synonym in synonyms))
#
# def compare_experts(
#     expert_rankings: pd.DataFrame,
#     synonyms: Dict[str, List[str]],
#     comparison: Callable[[str, str], bool] = lambda expert_opinion, synonym: expert_opinion.lower() == synonym.lower(),
# ) -> pd.Series:
#     """Compare the agreement between experts."""
#     data = {}
#     for expert in expert_rankings.columns:
#         data[expert] = find_category(expert_rankings[expert], synonyms[expert], comparison)
#
#     agreement = pd.DataFrame(data, index=expert_rankings.index)
#     agreement_percent = agreement.sum(axis=1) / agreement.shape[1]
#     agreement_percent.name = "Agreement Percentage"
#     return agreement_percent, agreement
#
# agreement_percent, agreement = compare_experts(expert_rankings, synonyms)
# ```
#
# ### Why this is a good idea
# - **Standardization**: By defining synonyms, we standardize the terminology used by different experts, making it easier to compare their ratings.
# - **Quantitative Analysis**: The agreement percentage provides a quantitative measure of how much the experts agree with each other.
# - **Identifying Discrepancies**: This method helps in identifying areas where experts disagree, which can be useful for further discussions and analysis.
#
# ### Potential Drawbacks
# - **Subjectivity**: The choice of synonyms is subjective and may not capture all nuances in the experts' ratings.
# - **Loss of Information**: Simplifying ratings into broader categories may result in the loss of detailed information.

data = {
    "Expert1": [
        "Relevant",
        "Irrelevant, Wind",
        "Relevant, Generic",
        "IDK",
        "Irrelevant",
    ],
    "Expert2": ["Relevant", "Rekevant", "Relevant", "IDK", "Irrelevant, Solar"],
    "Expert3": [
        "Relevant",
        "Irrelevant",
        "Relevant, Demand Side",
        "IDK",
        "Irrelevant, Generic",
    ],
}
expert_rankings = pd.DataFrame(data)

synonyms = {
    "Expert1": ["relevant"],
    "Expert2": ["Relevant", "Rekevant"],
    "Expert3": ["Relevant, Demand Side"],
}


def find_category(
    series: pd.Series,
    synonyms: List[str],
    comparison: Callable[[str, str], bool] = lambda expert_opinion, synonym: expert_opinion.lower() == synonym.lower(),
) -> pd.Series:
    """Replace synonyms with the unique value and create a boolean series."""
    return series.apply(lambda x: any(comparison(x, synonym) for synonym in synonyms))


def compare_experts(
    expert_rankings: pd.DataFrame,
    synonyms: Dict[str, List[str]],
    comparison: Callable[[str, str], bool] = lambda expert_opinion, synonym: expert_opinion.lower() == synonym.lower(),
) -> pd.Series:
    """Compare the agreement between experts."""
    data = {}
    for expert in expert_rankings.columns:
        data[expert] = find_category(expert_rankings[expert], synonyms[expert], comparison)

    agreement = pd.DataFrame(data, index=expert_rankings.index)
    agreement_percent = agreement.sum(axis=1) / agreement.shape[1]
    agreement_percent.name = "Agreement Percentage"
    return agreement_percent, agreement


agreement_percent, agreement = compare_experts(expert_rankings, synonyms)

agreement_table = pd.concat([agreement_percent, agreement], axis=1)
print("Example agreement table:")
print(agreement_table.to_string(index=False, header=True))
# %%

expert_rankings = pd.DataFrame(
    {
        "FEBNER": review_febner["FEBNER"].astype(str),
        "FOBERHAUSER": ranking_foberhau,
        "SKRITZIN": ranking_skritzin,
    },
    index=review_febner.index,
)

# Define synonyms for relevant and irrelevant papers
synonyms_relevant = {
    "FEBNER": [
        "Relevant",
        "Demand Side",
        "Relevant, Generic",
        "Relevant, Motivation & Impact",
        "Relevant, Data",
        "Relevant, Wind",
        "Relevant, Demand Side",
        "Rekevant",
        "Highly? Relevant",
        "Relevant, Motivation",
        "Relevant, close to 477",
        "No Opinion",  # no opinion = agree with other experts
    ],
    "FOBERHAUSER": ["1", "2"],
    "SKRITZIN": ["1", "2", "3"],
}

synonyms_irrelevant = {
    "FEBNER": [
        "Irrelevant",
        "Review, Generic",
        #    'No Opinion',  # no opinion = agree with other experts
    ],
    "FOBERHAUSER": ["3", "4", "5", "generic"],
    "SKRITZIN": ["4", "5"],
}

experts_agreement_relevant, _ = compare_experts(expert_rankings, synonyms_relevant)
experts_agreement_irrelevant, _ = compare_experts(expert_rankings, synonyms_irrelevant)

# %%


def plot_agreement(
    agreement_percentage: pd.Series,
    title: str = "Agreement Percentage Distribution (Relevant Papers)",
):
    """Plot the agreement percentage distribution."""
    plt.figure(figsize=(10, 6))
    sns.barplot(x=agreement_percentage.index, y=agreement_percentage.values)
    plt.title(title)
    plt.xlabel("Agreement Percentage")
    plt.ylabel("Count")
    plt.show()


# %%

plot_agreement(
    experts_agreement_relevant.value_counts(),
    title="Agreement Percentage Distribution (Relevant Papers)",
)
plot_agreement(
    experts_agreement_irrelevant.value_counts(),
    title="Agreement Percentage Distribution (Irrelevant Papers)",
)

# %% [markdown]
# ## Weather or Renewable Related Papers
# We check if the papers are related to weather or renewables.

weather_keywords = ["wind", "pv", "solar", "photovoltaic", "weather", "hydro"]
weather_related = (
    review_foberhau["manual_classification"].str.lower().str.contains("|".join(weather_keywords), case=False, na=False)
)

experts_relevant = pd.DataFrame(
    {
        "agreement": experts_agreement_relevant.values,
        "is_weather_related": weather_related,
        "classification": review_foberhau["manual_classification"],
    }
)
experts_irrelevant = pd.DataFrame(
    {
        "agreement": experts_agreement_irrelevant.values,
        "is_weather_related": weather_related,
        "classification": review_foberhau["manual_classification"],
    }
)


# %%
def process_categories(data: pd.Series, threshold: float = 3.0) -> pd.Series:
    """Process categories and mark less common categories as 'Other'."""
    all_categories = data.str.split(",").explode()
    category_counts = all_categories.value_counts()

    data = data.map(lambda x: x.split(",") if "," in x else [x])
    most_common_category = data.map(lambda category: max(category, key=lambda x: category_counts.get(x, 0)))

    category_translation = category_counts.apply(lambda x: x if x >= threshold else "Other")
    category_mapping = {
        category: (category if count != "Other" else "Other") for category, count in category_translation.items()
    }

    most_common_category = most_common_category.map(category_mapping)

    return most_common_category


# %%
def create_stacked_plot(
    data: pd.DataFrame,
    by: List[str] = ["agreement", "simple_categories"],
    *,
    ax: plt.Axes = None,
    size_threshold_container_size: int = 7,
) -> plt.Axes:
    """Create a stacked plot for the given data."""
    aggregated_data = data.groupby(by).size().unstack(fill_value=0)
    ax = aggregated_data.plot(kind="bar", stacked=True, figsize=(10, 6), colormap="tab20", ax=ax)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)

    for container in ax.containers:
        labels = [
            (f"{int(v.get_height())}" if v.get_height() > size_threshold_container_size else "") for v in container
        ]
        ax.bar_label(
            container,
            labels=labels,
            label_type="center",
            padding=3,
            fontsize=10,
            color="white",
        )

    ax.set_xticklabels([f"{x:.3f}" for x in aggregated_data.index], rotation=45)
    return ax


# %% [markdown]
# The next figure shows how much papers related to renewables and weather take up from the total set.
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 6))
create_stacked_plot(
    experts_relevant,
    by=["agreement", "is_weather_related"],
    ax=ax1,
)
ax1.legend(title="Weather Related")
ax1.set_xlabel("Agreement in %")
ax1.set_ylabel("Count")
ax1.set_title("Marked as Relevant Papers")

create_stacked_plot(
    experts_irrelevant,
    by=["agreement", "is_weather_related"],
    ax=ax2,
)
ax2.legend(title="Weather Related")
ax2.set_xlabel("Agreement in %")
ax2.set_ylabel("Count")
ax2.set_title("Marked as Irrelevant Papers")

fig.tight_layout()
fig.show()

# %% [markdown]
# Aggregate the data by agreement and category, without weather!
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 6))
data = experts_relevant[~experts_relevant["is_weather_related"]]["classification"]
data = data.map(lambda x: x.replace(" litr", "Literature Review"))
data = data.map(lambda x: x.replace(",Uncertainty", "Literature Review"))
experts_relevant["simple_categories"] = process_categories(data)
create_stacked_plot(experts_relevant, ax=ax1)
ax1.set_xlabel("Agreement in %")
ax1.set_ylabel("Count")
ax1.set_title("Marked as Relevant Papers")
ax1.legend(loc="upper center", bbox_to_anchor=(-0.5, 0.95))

data = experts_irrelevant[~experts_irrelevant["is_weather_related"]]["classification"]
data = data.map(lambda x: x.replace(" litr", "Literature Review"))
data = data.map(lambda x: x.replace(",Uncertainty", "Literature Review"))
experts_irrelevant["simple_categories"] = process_categories(data)
create_stacked_plot(experts_irrelevant, ax=ax2)
ax2.set_xlabel("Agreement in %")
ax2.set_ylabel("Count")
ax2.set_title("Marked as Irrelevant Papers")
ax2.legend(loc="center left", bbox_to_anchor=(1, 0.5))

fig.show()

# %% [markdown]
# ## Combining Opinions
# We select the threshold at >=0.6, which implies 2 out of 3 experts agree that the paper is relevant or irrelevant.

threshold = 0.6

all_papers = set(experts_agreement_relevant.index)
set_of_relevant_papers = set(experts_agreement_relevant[experts_agreement_relevant >= threshold].index)
set_of_irrelevant_papers = set(experts_agreement_irrelevant[experts_agreement_irrelevant >= threshold].index)
weather_related = experts_relevant[experts_relevant["is_weather_related"]].index

# only important papers
experts_selection = all_papers.intersection(set_of_relevant_papers).difference(set_of_irrelevant_papers)
relevant_weather_papers = all_papers.intersection(set_of_relevant_papers).intersection(weather_related)

# %%
data = experts_relevant["classification"]
data = data.loc[list(experts_selection)]
data = data.map(lambda x: x.replace(" litr", "Literature Review"))
data = data.map(lambda x: x.replace(",Uncertainty", "Literature Review"))

experts_relevant["simple_categories"] = process_categories(data)
ax = create_stacked_plot(experts_relevant)
ax.set_xlabel("Category")
ax.set_ylabel("Count")
ax.set_xticklabels(["Relevant", "Highly Relevant"], rotation=0)
ax.legend(loc="center left", bbox_to_anchor=(0.91, 0.5))
print(ax)

# %%

categoriesed = experts_relevant.loc[list(experts_selection)].apply(
    lambda x: "Highly Relevant" if x["agreement"] == 1 else "Relevant", axis=1
)

categoriesed_weather = experts_relevant.loc[list(weather_related.difference(experts_selection))].apply(
    lambda x: "Weather or Renewable Related", axis=1
)
categoriesed = pd.concat([categoriesed, categoriesed_weather])

categories = categoriesed.unique()
result = {category: set(categoriesed[categoriesed == category].index) for category in categories}

# Check for overlapping categories
all_indices = set()
for category, indices in result.items():
    if all_indices.intersection(indices):
        raise ValueError(f"Overlapping indices found in category: {category}")
    all_indices.update(indices)


# %%
def normalize_journal_name(name):
    # if an NA is found
    if pd.isna(name):
        return name

    # remove list brackets and quotes at the beginning and end
    name = re.sub(r"^\[|\]$", "", name)
    name = re.sub(r"^'|'$", "", name)
    name = name.replace('"', "").strip()
    return name


library = (
    review_foberhau.copy()
    .drop(
        columns=[
            "Unnamed: 0",
            "Ratind; 1=Very Relevant; 5=Irrelevant",
            "Ranking 1=Very Relevant; 5=Irrelevant",
            "Unnamed: 17",
            "FOBERHAU",
            "Kategorien",
        ]
    )
    .assign(journal_or_conference_name=lambda x: x["journal_or_conference_name"].apply(normalize_journal_name))
)


# ensure manually added papers are retained
manually_added = set(library[library["source"] == "Manual Search"].index)
manual_to_add = manually_added.difference(all_indices)
if manual_to_add:
    result["Manual Search"] = manual_to_add

with pd.ExcelWriter(ExpertReviewsRISC.agreement) as writer:
    for category, indices in result.items():
        category_papers = library.loc[list(indices)]
        category_papers.to_excel(writer, sheet_name=category)
# %%
