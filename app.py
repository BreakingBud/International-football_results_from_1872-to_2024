import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile
import os

# Define the file path and extraction directory
zip_file_path = 'football_data_matches_scorers_shootouts.zip'
extraction_dir = 'data/football_data/'

# Extract the zip file if it hasn't been extracted yet
if not os.path.exists(extraction_dir):
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extraction_dir)

# Load the datasets
@st.cache_data
def load_data():
    goalscorers_df = pd.read_csv(extraction_dir + 'goalscorers.csv')
    results_df = pd.read_csv(extraction_dir + 'results.csv')
    shootouts_df = pd.read_csv(extraction_dir + 'shootouts.csv')
    
    # Convert date columns to datetime format
    results_df['date'] = pd.to_datetime(results_df['date'])
    shootouts_df['date'] = pd.to_datetime(shootouts_df['date'])
    
    # Generate outcome column to indicate the match result
    results_df['outcome'] = results_df.apply(
        lambda row: row['home_team'] if row['home_score'] > row['away_score']
        else row['away_team'] if row['away_score'] > row['home_score'] else 'Draw',
        axis=1
    )
    
    # Merge results with shootouts to add shootout winner data
    merged_df = results_df.merge(
        shootouts_df[['date', 'home_team', 'away_team', 'winner']],
        on=['date', 'home_team', 'away_team'], 
        how='left'
    )
    
    # Add the shootout column: True if shootout occurred, False otherwise
    merged_df['shootout'] = merged_df['winner'].notna()
    
    return goalscorers_df, merged_df, shootouts_df

goalscorers_df, results_df, shootouts_df = load_data()

# Function to filter data for head-to-head analysis
def prepare_head_to_head_data(team1, team2, tournament, start_date, end_date):
    filtered_df = results_df[
        (((results_df['home_team'] == team1) & (results_df['away_team'] == team2)) |
        ((results_df['home_team'] == team2) & (results_df['away_team'] == team1))) &
        (results_df['tournament'].str.contains(tournament, case=False, na=False)) &
        (results_df['date'].between(start_date, end_date))
    ]
    return filtered_df

# Function to filter data for World Cup analysis
def prepare_world_cup_data(year):
    # Filter for FIFA World Cup matches of the selected year
    wc_df = results_df[
        (results_df['tournament'] == 'FIFA World Cup') &
        (results_df['date'].dt.year == year)
    ]
    
    if wc_df.empty:
        return None, None, None, None, None
    
    # Calculate statistics
    total_matches = wc_df.shape[0]
    total_goals = wc_df['home_score'].sum() + wc_df['away_score'].sum()
    total_teams = len(pd.unique(wc_df[['home_team', 'away_team']].values.ravel('K')))
    avg_goals_per_game = total_goals / total_matches if total_matches > 0 else 0
    
    # Extract final match stats
    final_match = wc_df.iloc[-1] if not wc_df.empty else None
    
    # Handle NaN winner or penalty shootout cases
    if final_match is not None and pd.isna(final_match['winner']):
        if final_match['shootout']:
            final_match['winner'] = f"Winner (Penalties): {final_match['home_team'] if final_match['home_score'] > final_match['away_score'] else final_match['away_team']}"
        else:
            final_match['winner'] = 'Draw'
    
    return total_matches, total_goals, total_teams, avg_goals_per_game, final_match

# Set up the sidebar menu
st.sidebar.title("Navigation")
menu = st.sidebar.radio(
    "Go to",
    ("Introduction", "Head-to-Head Analysis", "World Cup Analysis")
)

if menu == "Introduction":
    st.title("Football Analysis App")
    st.markdown("""
    ### Welcome to the Football Analysis App
    
    This application allows you to explore historical football match data, particularly focusing on head-to-head matchups between different teams and World Cup analysis.
    
    Use the sidebar to navigate to different sections of the app.
    """)
    
elif menu == "Head-to-Head Analysis":
    # Define columns for layout
    col1, col2 = st.columns([1, 2], gap="large")

    with col1:
        # Team selection
        team1 = st.selectbox('Select Team 1', results_df['home_team'].unique())
        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
        team2 = st.selectbox('Select Team 2', results_df['home_team'].unique())
        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
        
        # Tournament selection
        tournament = st.selectbox('Select Tournament', ['All'] + sorted(results_df['tournament'].unique().tolist()))
        if tournament == 'All':
            tournament = ''  # Empty string will be used to match all tournaments
        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

        # Date range selection
        min_date = results_df['date'].min().to_pydatetime()
        max_date = results_df['date'].max().to_pydatetime()
        date_range = st.slider(
            'Select Date Range',
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date),
            format="YYYY-MM-DD"
        )

        start_date, end_date = date_range

    with col2:
        # Perform analysis
        head_to_head_df = prepare_head_to_head_data(team1, team2, tournament, start_date, end_date)

        total_matches = len(head_to_head_df)
        st.markdown(f"**{team1}** and **{team2}** played **{total_matches}** matches head to head across all tournaments.")
        
        if tournament:
            st.markdown(f"Filtering by tournament: **{tournament}**")

        # Label outcomes correctly
        head_to_head_df['outcome_label'] = head_to_head_df['outcome'].apply(
            lambda x: f'{team1} Win' if x == team1 else f'{team2} Win' if x == team2 else 'Draw'
        )

        # Correctly count unique outcomes
        outcome_counts = head_to_head_df['outcome_label'].value_counts(dropna=False)

        # Pie chart for outcomes
        fig = px.pie(outcome_counts, names=outcome_counts.index, values=outcome_counts.values, title="Win Rate")
        st.plotly_chart(fig, use_container_width=True)

        # Display shootout data
        shootout_matches = head_to_head_df[head_to_head_df['shootout'] == True]
        if not shootout_matches.empty:
            st.markdown("### Shootout Matches:")
            st.dataframe(shootout_matches[['date', 'home_team', 'away_team', 'winner']], use_container_width=True)

elif menu == "World Cup Analysis":
    st.title("World Cup Analysis")

    # Year selection - only show years where FIFA World Cup was held
    world_cup_years = sorted(results_df[results_df['tournament'] == 'FIFA World Cup']['date'].dt.year.unique())
    year = st.selectbox('Select Year of World Cup', world_cup_years)

    # Get World Cup statistics for the selected year
    total_matches, total_goals, total_teams, avg_goals_per_game, final_match = prepare_world_cup_data(year)

    if total_matches is None:
        st.markdown(f"### No data available for FIFA World Cup {year}.")
    else:
        # Display statistics
        st.markdown(f"### World Cup {year} Overview")
        st.markdown(f"**Total Matches:** {total_matches}")
        st.markdown(f"**Total Goals:** {total_goals}")
        st.markdown(f"**Total Teams Participated:** {total_teams}")
        st.markdown(f"**Average Goals Per Game:** {avg_goals_per_game:.2f}")
        
        if final_match is not None:
            st.markdown("### Final Match Stats")
            st.markdown(f"**Date:** {final_match['date'].strftime('%Y-%m-%d')}")
            st.markdown(f"**Teams:** {final_match['home_team']} vs {final_match['away_team']}")
            st.markdown(f"**Score:** {final_match['home_team']} {final_match['home_score']} - {final_match['away_score']} {final_match['away_team']}")
            st.markdown(f"**Winner:** {final_match['winner']}")
