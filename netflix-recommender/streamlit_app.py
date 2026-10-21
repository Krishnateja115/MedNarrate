"""Minimal Streamlit interface for the notebook's Netflix recommender."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent))
from recommender import CustomTitle, RecommendationResult, Recommender, load_catalog


st.set_page_config(
    page_title="Netflix Catalog Lab", page_icon="🎬", layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root { color-scheme: light; }
    .stApp { background: #faf9f7; color: #202022; }
    .block-container { max-width: 1120px; padding-top: 2.1rem; }
    h1, h2, h3 { letter-spacing: -.035em; }
    h1 { font-size: 2.9rem !important; }
    .eyebrow { color: #bd303c; font-size: .76rem; font-weight: 750;
        letter-spacing: .14em; text-transform: uppercase; }
    .subtle { color: #68686e; font-size: 1.03rem; }
    .result-card { background: white; border: 1px solid #e7e4df;
        border-radius: 14px; padding: 1.1rem 1.25rem; margin: .55rem 0; }
    .result-title { font-size: 1.08rem; font-weight: 720; margin: 0 0 .18rem; }
    .result-meta { color: #696971; font-size: .9rem; margin: 0; }
    .score { color: #b62634; font-weight: 760; }
    div.stButton > button[kind="primary"], div.stFormSubmitButton > button[kind="primary"] {
        background: #bc2937; border-color: #bc2937; border-radius: 9px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner="Preparing the catalog model…")
def get_model() -> Recommender:
    """Load and fit once for all Streamlit sessions."""
    return Recommender(load_catalog())


def clean_html(value: object) -> str:
    """Escape dataset or user text before rendering card HTML."""
    import html

    return html.escape(str(value))


def score_chart(result: RecommendationResult) -> go.Figure:
    """Show notebook cosine scores for each recommended dataset title."""
    matches = result.matches.iloc[::-1]
    figure = go.Figure(
        go.Bar(
            x=matches["similarity"], y=matches["title"], orientation="h",
            marker_color="#bb303d",
            hovertemplate="%{y}<br>Cosine similarity: %{x:.3f}<extra></extra>",
        )
    )
    figure.update_layout(
        height=max(300, 58 * len(matches) + 95),
        margin=dict(l=12, r=18, t=15, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(range=[0, 1], title="Cosine similarity", gridcolor="#e9e5e0"),
        yaxis=dict(title="", automargin=True),
        font=dict(color="#35353a"),
        showlegend=False,
    )
    return figure


def genre_chart(result: RecommendationResult) -> go.Figure:
    """Compare actual genre labels in the dataset with the input genres."""
    matches = result.matches.iloc[::-1]
    figure = go.Figure(
        go.Bar(
            x=matches["genre_overlap"], y=matches["title"], orientation="h",
            marker_color="#555a66",
            hovertemplate="%{y}<br>Genre overlap: %{x:.0%}<extra></extra>",
        )
    )
    figure.update_layout(
        height=max(300, 58 * len(matches) + 95),
        margin=dict(l=12, r=18, t=15, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(range=[0, 1], title="Genre overlap · Jaccard", gridcolor="#e9e5e0"),
        yaxis=dict(title="", automargin=True),
        font=dict(color="#35353a"),
        showlegend=False,
    )
    return figure


def duration_chart(result: RecommendationResult, catalog: pd.DataFrame) -> go.Figure:
    """Plot actual runtimes or seasons for the input and recommendations."""
    content_type = str(result.query["type"])
    filtered = result.matches[result.matches["type"].eq(content_type)]
    values = filtered["duration_num"].tolist()
    labels = filtered["title"].tolist()
    colors = ["#777b85"] * len(values)
    if result.source == "catalog":
        values.insert(0, float(result.query["duration_num"]))
        labels.insert(0, f"Input · {result.query['title']}")
        colors.insert(0, "#bb303d")
    median = catalog.loc[catalog["type"].eq(content_type), "duration_num"].median()
    unit = "minutes" if content_type == "Movie" else "seasons"
    figure = go.Figure(
        go.Bar(x=labels, y=values, marker_color=colors,
               hovertemplate=f"%{{x}}<br>%{{y:.0f}} {unit}<extra></extra>")
    )
    figure.add_hline(
        y=float(median), line_dash="dash", line_color="#22262b",
        annotation_text=f"Catalog median · {median:.0f} {unit}",
        annotation_position="top left",
    )
    figure.update_layout(
        height=365, margin=dict(l=12, r=15, t=35, b=50),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(title=unit.title(), gridcolor="#e9e5e0"),
        xaxis=dict(title="", tickangle=-25, automargin=True),
        font=dict(color="#35353a"), showlegend=False,
    )
    return figure


def render_results(result: RecommendationResult, catalog: pd.DataFrame) -> None:
    st.divider()
    st.markdown('<p class="eyebrow">Your results</p>', unsafe_allow_html=True)
    st.header(f"Titles similar to {result.query['title']}")
    st.caption(
        "These are model-ranked catalog titles. Similarity measures metadata resemblance, "
        "not a viewing rating or a probability."
    )

    left, right = st.columns([1.3, 1], gap="large")
    with left:
        st.subheader("Model ranking")
        st.plotly_chart(score_chart(result), use_container_width=True)
    with right:
        st.subheader("Genre match")
        st.plotly_chart(genre_chart(result), use_container_width=True)

    st.subheader("Recommended titles")
    for rank, row in result.matches.iterrows():
        title = clean_html(row["title"])
        details = " · ".join(
            [str(row["type"]), str(row["release_year"]), str(row["rating"]),
             str(row["primary_genre"]), str(row["duration"])]
        )
        st.markdown(
            '<div class="result-card">'
            f'<p class="result-title">{rank + 1:02d}. {title} '
            f'<span class="score">{row["similarity"]:.1%} similar</span></p>'
            f'<p class="result-meta">{clean_html(details)}</p>'
            f'<p class="result-meta">{clean_html(row["description"])}</p>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.subheader("Compared with the dataset")
    st.caption(
        "Bars below are actual recorded durations of titles in the dataset. "
        "The dashed line is the median for the input's content type."
    )
    same_type = result.matches["type"].eq(str(result.query["type"])).any()
    if same_type:
        st.plotly_chart(duration_chart(result, catalog), use_container_width=True)
    else:
        st.info("Select matching content types to compare durations in the same units.")
    if result.source == "custom":
        st.caption("A new title has no recorded runtime or seasons in this dataset.")


def discover(model: Recommender) -> None:
    st.markdown('<p class="eyebrow">Notebook model · Team 13</p>', unsafe_allow_html=True)
    st.title("Find your next watch")
    st.markdown(
        '<p class="subtle">Explore similar Netflix titles using the project’s '
        'content based recommendation model.</p>', unsafe_allow_html=True,
    )
    st.write("")
    mode = st.segmented_control(
        "Start with", ["A catalog title", "A new idea"],
        default="A catalog title",
    )
    type_filter = st.selectbox("Show recommendations for", ["Any type", "Movie", "TV Show"])
    selected_type = None if type_filter == "Any type" else type_filter
    count = st.slider("Number of recommendations", min_value=3, max_value=10, value=5)

    if mode == "A catalog title":
        titles = model.catalog["title"].astype(str).tolist()
        default = titles.index("Ganglands") if "Ganglands" in titles else 0
        index = st.selectbox(
            "Choose a title", range(len(titles)), index=default,
            format_func=lambda value: f"{titles[value]} · {model.catalog.iloc[value]['type']}",
        )
        row = model.catalog.iloc[index]
        st.caption(
            f"{row['type']} · {row['release_year']} · {row['rating']} · "
            f"{row['listed_in']}"
        )
        if st.button("Find similar titles", type="primary"):
            st.session_state["result"] = model.recommend_existing(
                index, count=count, content_type=selected_type
            )
    else:
        with st.form("new_title"):
            st.caption("Describe a title using the same fields the notebook model learned from.")
            title = st.text_input("Title", placeholder="My new title")
            content_type = st.selectbox("Format", ["Movie", "TV Show"])
            genres = st.text_input("Genres", placeholder="Dramas, International Movies")
            director = st.text_input("Director", placeholder="Optional")
            cast = st.text_input("Cast", placeholder="Separate names with commas")
            rating = st.selectbox(
                "Age rating", ["TV-MA", "TV-14", "TV-PG", "PG-13", "R", "PG", "G", "NR"]
            )
            description = st.text_area(
                "Synopsis", placeholder="What happens in the story?", height=110
            )
            submitted = st.form_submit_button("Find similar titles", type="primary")
        if submitted:
            try:
                custom = CustomTitle(
                    title=title, content_type=content_type, genres=genres,
                    director=director, cast=cast, rating=rating,
                    description=description,
                )
                st.session_state["result"] = model.recommend_custom(
                    custom, count=count, content_type=selected_type
                )
            except (ValidationError, ValueError) as error:
                st.error(str(error))

    result = st.session_state.get("result")
    if result is not None:
        render_results(result, model.catalog)


def explore(catalog: pd.DataFrame) -> None:
    st.markdown('<p class="eyebrow">The source dataset</p>', unsafe_allow_html=True)
    st.title("Inside the catalog")
    st.caption("Netflix Movies and TV Shows dataset · catalog snapshot through 2021")
    first, second, third = st.columns(3)
    first.metric("Titles", f"{len(catalog):,}")
    second.metric("Movies", f"{catalog['type'].eq('Movie').sum():,}")
    third.metric("TV shows", f"{catalog['type'].eq('TV Show').sum():,}")
    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Catalog by type")
        counts = catalog["type"].value_counts()
        figure = go.Figure(
            go.Bar(x=counts.index, y=counts.values, marker_color=["#bb303d", "#555a66"])
        )
        figure.update_layout(
            height=340, margin=dict(l=10, r=10, t=10, b=25),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(title="Titles", gridcolor="#e9e5e0"),
        )
        st.plotly_chart(figure, use_container_width=True)
    with right:
        st.subheader("Top genres")
        genres = catalog["primary_genre"].value_counts().head(8).iloc[::-1]
        figure = go.Figure(
            go.Bar(x=genres.values, y=genres.index, orientation="h", marker_color="#555a66")
        )
        figure.update_layout(
            height=340, margin=dict(l=10, r=10, t=10, b=25),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(title="Titles", gridcolor="#e9e5e0"),
            yaxis=dict(title="", automargin=True),
        )
        st.plotly_chart(figure, use_container_width=True)
    st.subheader("How the recommendations work")
    st.write(
        "The notebook combines each title’s genres, director, first three cast members, "
        "rating, and synopsis. TF IDF turns those words into a vector; cosine similarity "
        "ranks catalog titles. The model has no viewer ratings, watch history, or known "
        "correct recommendation label."
    )


def main() -> None:
    try:
        model = get_model()
    except (FileNotFoundError, ValueError) as error:
        st.error(f"The catalog could not be loaded: {error}")
        st.stop()
    tab_discover, tab_explore = st.tabs(["Discover", "Explore dataset"])
    with tab_discover:
        discover(model)
    with tab_explore:
        explore(model.catalog)


if __name__ == "__main__":
    main()
