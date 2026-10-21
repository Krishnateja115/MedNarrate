"""Notebook-faithful Netflix metadata recommendation service."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, model_validator
from sklearn.feature_extraction.text import TfidfVectorizer


DATA_PATH = Path(__file__).parent / "data" / "netflix_titles.csv"


class CustomTitle(BaseModel):
    """A new title described using the notebook's model features."""

    title: str = Field(min_length=1, max_length=150)
    content_type: Literal["Movie", "TV Show"]
    genres: str = Field(default="", max_length=250)
    director: str = Field(default="", max_length=200)
    cast: str = Field(default="", max_length=400)
    rating: str = Field(default="", max_length=30)
    description: str = Field(default="", max_length=1500)

    @model_validator(mode="after")
    def require_metadata(self) -> "CustomTitle":
        if not any(
            value.strip()
            for value in (self.genres, self.director, self.cast, self.description)
        ):
            raise ValueError("Add a genre, director, cast member, or synopsis.")
        return self


def _clean_entity(value: object, max_items: int | None = None) -> str:
    if pd.isna(value) or str(value).strip().lower() == "unknown":
        return ""
    items = str(value).split(",")
    if max_items is not None:
        items = items[:max_items]
    return " ".join(re.sub(r"\s+", "", item).lower().strip() for item in items)


def _clean_synopsis(value: object) -> str:
    if pd.isna(value):
        return ""
    return " ".join(re.sub(r"[^a-zA-Z0-9\s]", " ", str(value).lower()).split())


def metadata_soup(
    genres: str, director: str, cast: str, rating: str, description: str
) -> str:
    """Match the feature order and weights in notebook cell 107."""
    genre = _clean_entity(genres)
    director_token = _clean_entity(director)
    cast_token = _clean_entity(cast, max_items=3)
    rating_token = str(rating).lower().replace("-", "")
    synopsis = _clean_synopsis(description)
    return (
        (genre + " ") * 3
        + (director_token + " ") * 2
        + cast_token
        + " "
        + rating_token
        + " "
        + synopsis
    )


def load_catalog(path: Path = DATA_PATH) -> pd.DataFrame:
    """Apply the notebook's metadata repairs and derive display fields."""
    frame = pd.read_csv(path)
    expected = {
        "show_id", "type", "title", "director", "cast", "country",
        "date_added", "release_year", "rating", "duration", "listed_in",
        "description",
    }
    missing = expected.difference(frame.columns)
    if missing:
        raise ValueError(f"Dataset is missing columns: {', '.join(sorted(missing))}")
    frame = frame.reset_index(drop=True)
    for column in ("director", "cast", "country"):
        frame[column] = frame[column].fillna("Unknown")
    misplaced = frame["rating"].astype(str).str.contains("min", na=False)
    frame.loc[misplaced, "duration"] = frame.loc[misplaced, "rating"]
    frame.loc[misplaced, "rating"] = np.nan
    frame["rating"] = frame["rating"].fillna(frame["rating"].mode().iloc[0])
    frame["duration_num"] = pd.to_numeric(
        frame["duration"].astype(str).str.extract(r"(\d+)")[0],
        errors="coerce",
    )
    for content_type in ("Movie", "TV Show"):
        mask = frame["type"].eq(content_type)
        frame.loc[mask, "duration_num"] = frame.loc[mask, "duration_num"].fillna(
            frame.loc[mask, "duration_num"].median()
        )
    frame["primary_genre"] = (
        frame["listed_in"].fillna("Unknown").str.split(",").str[0].str.strip()
    )
    frame["primary_country"] = (
        frame["country"].str.strip(" ,").str.split(",").str[0].str.strip()
    )
    frame["year_added"] = pd.to_datetime(
        frame["date_added"].fillna(frame["date_added"].mode().iloc[0]).str.strip(),
        errors="coerce",
    ).dt.year
    frame["soup"] = [
        metadata_soup(genre, director, cast, rating, description)
        for genre, director, cast, rating, description in zip(
            frame["listed_in"], frame["director"], frame["cast"],
            frame["rating"], frame["description"]
        )
    ]
    return frame


def genre_overlap(left: str, right: str) -> float:
    """Jaccard overlap of the actual dataset genre labels."""
    first = {item.strip().lower() for item in left.split(",") if item.strip()}
    second = {item.strip().lower() for item in right.split(",") if item.strip()}
    union = first | second
    return len(first & second) / len(union) if union else 0.0


@dataclass(frozen=True)
class RecommendationResult:
    query: dict[str, object]
    matches: pd.DataFrame
    source: Literal["catalog", "custom"]


class Recommender:
    """Fit the notebook model once and score one query at a time."""

    def __init__(self, catalog: pd.DataFrame) -> None:
        self.catalog = catalog.reset_index(drop=True)
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.8,
            sublinear_tf=True,
        )
        self.matrix = self.vectorizer.fit_transform(self.catalog["soup"])

    def recommend_existing(
        self, index: int, count: int = 5, content_type: str | None = None
    ) -> RecommendationResult:
        if not 0 <= index < len(self.catalog):
            raise ValueError("Choose a title from the catalog.")
        row = self.catalog.iloc[index]
        query = {
            "title": row["title"], "type": row["type"],
            "listed_in": row["listed_in"], "rating": row["rating"],
            "release_year": int(row["release_year"]),
            "duration_num": float(row["duration_num"]),
            "duration": row["duration"], "description": row["description"],
        }
        scores = (self.matrix[index] @ self.matrix.T).toarray().ravel()
        scores[index] = -1.0
        matches = self._rank(scores, str(row["listed_in"]), count, content_type)
        return RecommendationResult(query, matches, "catalog")

    def recommend_custom(
        self, title: CustomTitle, count: int = 5, content_type: str | None = None
    ) -> RecommendationResult:
        soup = metadata_soup(
            title.genres, title.director, title.cast, title.rating,
            title.description,
        )
        vector = self.vectorizer.transform([soup])
        if vector.nnz == 0:
            raise ValueError(
                "The description contains no terms found in this catalog. "
                "Add a genre or a longer synopsis."
            )
        scores = (vector @ self.matrix.T).toarray().ravel()
        query = {
            "title": title.title, "type": title.content_type,
            "listed_in": title.genres, "rating": title.rating,
            "description": title.description,
        }
        matches = self._rank(scores, title.genres, count, content_type)
        return RecommendationResult(query, matches, "custom")

    def _rank(
        self, scores: np.ndarray, query_genres: str, count: int,
        content_type: str | None,
    ) -> pd.DataFrame:
        if not 1 <= count <= 20:
            raise ValueError("Recommendation count must be between 1 and 20.")
        if content_type not in (None, "Movie", "TV Show"):
            raise ValueError("Unknown content type filter.")
        eligible = np.arange(len(scores))
        if content_type:
            eligible = eligible[self.catalog["type"].to_numpy()[eligible] == content_type]
        eligible = eligible[scores[eligible] >= 0]
        ranked = eligible[np.argsort(-scores[eligible], kind="stable")[:count]]
        columns = [
            "title", "type", "primary_genre", "listed_in", "director",
            "release_year", "rating", "duration", "duration_num",
            "description", "show_id",
        ]
        result = self.catalog.iloc[ranked][columns].copy().reset_index(drop=True)
        result.insert(1, "similarity", scores[ranked].astype(float))
        result.insert(
            2, "genre_overlap",
            [genre_overlap(query_genres, value) for value in result["listed_in"]],
        )
        return result
