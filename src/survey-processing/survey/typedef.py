import pandera.pandas as pa
from pandera.pandas import DataFrameModel
from pandera.typing import Series


class EntryDataFrameSchema(DataFrameModel):
    within_file_index: Series[int]
    file_name: Series[str]
    source: Series[str]

    # we care about these a lot
    title: Series[str]
    authors: Series[str]
    year: Series[int]
    doi: Series[pa.String]
    url: Series[pa.String]  # should contain a link to the article on the publisher website
    abstract: Series[pa.String]
    publisher: Series[pa.String]
    cites: Series[pa.Int]
    document_type: Series[pa.String]  # Article, Journal, ...
    journal_or_conference_name: Series[pa.String]

    # these are manually added by reviewers
    manual_classification: Series[pa.String]  # comma separated list of classifications


entry_data_frame_order = [
    EntryDataFrameSchema.within_file_index,
    EntryDataFrameSchema.file_name,
    EntryDataFrameSchema.source,
    EntryDataFrameSchema.title,
    EntryDataFrameSchema.authors,
    EntryDataFrameSchema.year,
    EntryDataFrameSchema.doi,
    EntryDataFrameSchema.url,
    EntryDataFrameSchema.abstract,
    EntryDataFrameSchema.publisher,
    EntryDataFrameSchema.cites,
    EntryDataFrameSchema.document_type,
    EntryDataFrameSchema.journal_or_conference_name,
    EntryDataFrameSchema.manual_classification,
]
