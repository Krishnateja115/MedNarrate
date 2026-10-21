# Netflix catalog recommender

This app reproduces the content-based recommendation model in `Team13_LE2.ipynb`.
It uses the notebook's metadata soup (genres repeated three times, director twice,
top three cast members, rating, description), sublinear TF-IDF with English stop
words and 1–2 grams, and cosine similarity. The app calculates only the query's
similarity vector, avoiding the notebook's large all-pairs matrix.

## Run locally

```bash
pip install -r netflix-recommender/requirements.txt
streamlit run netflix-recommender/streamlit_app.py
```

The bundled `data/netflix_titles.csv` is the original 8,807-row dataset. No
training job, API key, or external service is required. The model is fit once
per Streamlit process and cached.

## Deploy on Streamlit Community Cloud

Select the repository, `main` branch, and entrypoint
`netflix-recommender/streamlit_app.py`. Streamlit will install the adjacent
`requirements.txt`. The dataset must stay in `netflix-recommender/data/`.

## Reading results

Similarity is a model score, not a predicted user rating or probability of
enjoyment. The notebook contains no user outcomes or supervised target, so an
actual-versus-predicted error chart would be misleading. The app instead shows
model scores, actual catalog metadata, genre overlap, and comparisons with
dataset distributions. For a new title, the model uses only genre, director,
cast, age rating, and synopsis, matching the notebook.
