import csv
from pathlib import Path


def difference(path: Path) -> float:
    rows = list(csv.DictReader(path.open()))
    treatment = [float(row["yield"]) for row in rows if row["group"] == "treatment"]
    control = [float(row["yield"]) for row in rows if row["group"] == "control"]
    return sum(treatment) / len(treatment) - sum(control) / len(control)


def delegated_analysis(source: str) -> None:
    exec(source)


value = difference(Path("data.csv"))
