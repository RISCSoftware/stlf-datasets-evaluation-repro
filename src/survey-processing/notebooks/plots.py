# %%
# Data for the bar plot
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Data for the bar plot
data = {
    "Source": ["Scopus", "Scholar", "IEEE Xplore", "CSDL", "ACM"],
    "Count": [527, 4503, 83, 1486, 243],
}

# Convert the data to a DataFrame for seaborn
df = pd.DataFrame(data)

# Sort the DataFrame by the 'Count' column in descending order
df = df.sort_values(by="Count", ascending=False)

# Set the seaborn style
sns.set(style="whitegrid")

# Create the bar plot
plt.figure(figsize=(10, 6))
bar_plot = sns.barplot(x="Source", y="Count", data=df)

# Add labels and title
bar_plot.set_xlabel("Source", fontsize=14, weight="bold")
bar_plot.set_ylabel("Number of Papers", fontsize=14, weight="bold")
bar_plot.set_title(
    f'Records identified by Datasource (n = {sum(data["Count"])})',
    fontsize=16,
    weight="bold",
)

# Customize the appearance
bar_plot.tick_params(axis="x", labelsize=12)
bar_plot.tick_params(axis="y", labelsize=12)
bar_plot.grid(True, which="both", linestyle="--", linewidth=0.5)

# Add the count labels on top of the bars
for p in bar_plot.patches:
    bar_plot.annotate(
        format(p.get_height(), ".0f"),
        (p.get_x() + p.get_width() / 2.0, p.get_height()),
        ha="center",
        va="center",
        xytext=(0, 9),  # 9 points vertical offset
        textcoords="offset points",
        fontsize=12,
    )

# Show the plot
plt.tight_layout()

# Show the plot
plt.show()
# %%
