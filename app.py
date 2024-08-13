import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile
import os

# Define the file path and extraction directory
zip_file_path = 'football_data_matches_scorers_shootouts.zip'
extraction_dir = 'data/football_data/'

# Extract the zip file
if not os.path.exists(extraction_dir):
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extraction_dir)

# Load the datasets
@st.cache_data
def load_data():
    goalscorers_df = pd.read_csv(extraction_dir + 'goalscorers.csv')
    results_df = pd.read_csv(extraction_dir + 'results.csv')
    shootouts_df = pd.read_csv(extraction_dir + 'shootouts.csv')
    return goalscorers_df, results_df, shootouts_df

goalscorers_df, results_df, shootouts_df = load_data()

# Prepare data for head-to-head analysis
def prepare_head_to_head_data(team1, team2, tournament, start_date, end_date):
    filtered_df = results_df[
        (((results_df['home_team'] == team1) & (results_df['away_team'] == team2)) |
        ((results_df['home_team'] == team2) & (results_df['away_team'] == team1))) &
        (results_df['tournament'].str.contains(tournament)) &
        (results_df['date'].between(start_date, end_date))
    ]
    return filtered_df

# Set up the sidebar menu
st.sidebar.title("Navigation")
menu = st.sidebar.radio(
    "Go to",
    ("Introduction", "Head-to-Head Analysis")
)

if menu == "Introduction":
    st.title("Football Analysis App")
    st.write("Welcome to the Football Analysis App. Use the sidebar to navigate to different sections of the app.")
    
elif menu == "Head-to-Head Analysis":
    st.title("Head-to-Head Analysis")

    # Team selection
    team1 = st.selectbox('Select Team 1', results_df['home_team'].unique())
    team2 = st.selectbox('Select Team 2', results_df['home_team'].unique())
    
    # Tournament selection
    tournament = st.text_input('Select Tournament (Leave blank for all)', '')
    
    # Date range selection
    date_range = st.slider(
        'Select Date Range',
        min_value=results_df['date'].min(),
        max_value=results_df['date'].max(),
        value=(results_df['date'].min(), results_df['date'].max())
    )

    start_date, end_date = date_range

    # Perform analysis
    head_to_head_df = prepare_head_to_head_data(team1, team2, tournament, start_date, end_date)

    total_matches = len(head_to_head_df)
    st.write(f"{team1} and {team2} played {total_matches} matches head to head across all tournaments.")
    
    if tournament:
        st.write(f"Filtering by tournament: {tournament}")

    # Pie chart for outcomes
    outcome_counts = head_to_head_df['outcome'].value_counts()
    fig = px.pie(outcome_counts, names=outcome_counts.index, values=outcome_counts.values, title="Head-to-Head Win Rate")
    st.plotly_chart(fig)

    # Display shootout data
    shootout_matches = head_to_head_df[head_to_head_df['shootout'] == True]
    if not shootout_matches.empty:
        st.write("Shootout Matches:")
        st.dataframe(shootout_matches[['date', 'home_team', 'away_team', 'winner']])
    else:
        st.write("No shootout data available for these teams in the selected range.")

