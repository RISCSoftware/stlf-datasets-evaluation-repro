from pathlib import Path


class Paths:
    data_dir: Path = Path(__file__).parent.parent / "data"

    total_library = data_dir / "total_library.xlsx"
    library_file: Path = data_dir / "library.xlsx"
    # this is the initial library filtered by @dfalkner
    filtered_library_file: Path = data_dir / "filtered_library.xlsx"
    # this is the final library, after filtering by @dfalkner, including extra sources
    initial_screened_library: Path = data_dir / "initial_screened_library.xlsx"
    # this is the enriched library for data scientists
    enriched_library: Path = data_dir / "enriched_library.xlsx"

    csdl_file: Path = data_dir / "csdl.xlsx"
    filtered_csdl_file: Path = data_dir / "filtered_csdl.xlsx"

    acm_bib_file: Path = data_dir / "acm.bib"
    acm_file_raw: Path = data_dir / "acm_raw.xlsx"
    acm_file: Path = data_dir / "acm.xlsx"

    manual_classification_map: Path = data_dir / "manual_classification_map.jsonc"


class ExpertReviewsRISC:
    base_dir = Paths.data_dir / "expert_reviews_risc"

    febner = base_dir / "library_review_febner.xlsx"
    foberhau = base_dir / "library_review_foberhau.xlsx"
    skritzin = base_dir / "library_review_skritzin.xlsx"

    agreement = base_dir / "agreement.xlsx"
    datasets = base_dir / "datasets.xlsx"
    models_with_papers = base_dir / "models_with_papers.xlsx"
    chips = base_dir / "chips.json"
