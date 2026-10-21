"""Checks for the real notebook data and inference path."""

from pathlib import Path
import sys

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from recommender import CustomTitle, Recommender, genre_overlap, load_catalog


@pytest.fixture(scope="module")
def model() -> Recommender:
    return Recommender(load_catalog())


def test_catalog_and_existing_query(model: Recommender) -> None:
    assert len(model.catalog) == 8807
    index = int(model.catalog.index[model.catalog["title"].eq("Ganglands")][0])
    result = model.recommend_existing(index, count=5, content_type="TV Show")
    assert result.query["title"] == "Ganglands"
    assert len(result.matches) == 5
    assert result.matches["type"].eq("TV Show").all()
    assert "Ganglands" not in result.matches["title"].tolist()
    assert result.matches["similarity"].between(0, 1).all()
    assert result.matches["similarity"].is_monotonic_decreasing


def test_custom_query_and_comparison(model: Recommender) -> None:
    title = CustomTitle(
        title="A crime series", content_type="TV Show",
        genres="Crime TV Shows, International TV Shows",
        description="A skilled thief protects his family from a criminal gang.",
    )
    result = model.recommend_custom(title, count=4, content_type="TV Show")
    assert len(result.matches) == 4
    assert result.matches["genre_overlap"].between(0, 1).all()
    assert result.matches["similarity"].max() > 0
    assert genre_overlap("Dramas, Comedies", "Comedies, Children & Family Movies") == pytest.approx(1 / 3)


def test_validation_and_bad_query(model: Recommender) -> None:
    with pytest.raises(ValidationError):
        CustomTitle(title="Empty", content_type="Movie")
    with pytest.raises(ValueError, match="Choose a title"):
        model.recommend_existing(-1)
    with pytest.raises(ValueError, match="no terms"):
        model.recommend_custom(
            CustomTitle(
                title="Unknown", content_type="Movie",
                description="qzxvjkq qzxvjkq qzxvjkq",
            )
        )
