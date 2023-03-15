import pandas as pd

def extract_users_artists(path_data: str, min_weight: int) -> pd.DataFrame:
    df = pd.read_csv(path_data, sep="\t")

    # Keep weight greater than 100
    return df[df['weight'] > min_weight]

def create_normalize_matrix(df: pd.DataFrame) -> pd.DataFrame:
    # Create a matrix user artist weight
    matrix = df.pivot_table(index='userID', columns='artistID', values='weight')

    # Normalize matrix
    matrix_norm = (matrix - matrix.mean()) / matrix.std()

    return matrix_norm

def recommended_artists(df_similars_users_artists: pd.DataFrame, df_similars_users: pd.DataFrame):
    artists_score = {}

    # Loop through artists
    for i in df_similars_users_artists.columns:
        # Get the weight for artist i
        artist_weight = df_similars_users_artists[i]

        # Create a variable to store the score
        total = 0

        # Create a variable to store the number of scores
        count = 0

        # Loop through similar users
        for u in df_similars_users.index:

            # If the artist has rating
            if pd.isna(artist_weight[u]) == False:
                # Score is the sum of user similarity score multiply by the artist rating
                score = df_similars_users[u] * artist_weight[u]

                # Add the score to the total score for the artist so far
                total += score

                # Add 1 to the count
                count +=1

        # Get the average score for the item
        artists_score[i] = total / count

    # Convert dictionary to pandas dataframe
    artists_score = pd.DataFrame(artists_score.items(), columns=['artistID', 'score'])
    
    # Sort the artists by score
    return artists_score.sort_values(by='score', ascending=False)

def get_artists_to_listen_by_user(user_id: int):
    
    ua_df = extract_users_artists('users_artists.dat', 100)

    matrix_norm = create_normalize_matrix(ua_df)

    # User similarity using Pearson correlation
    matrix_user_similarity = matrix_norm.T.corr()

    # Get similars users
    similars_users = matrix_user_similarity[matrix_user_similarity[user_id]>0.5][user_id].sort_values(ascending=False)[:10]

    # Get artists that have been listened by the user
    user_listen = matrix_norm[matrix_norm.index == user_id].dropna(axis=1, how='all')
    
    # Get artists that none of the similar users have listened
    similars_users_artists = matrix_norm[matrix_norm.index.isin(similars_users.index)].dropna(axis=1, how='all')

    # Remove the listened artists from the artists list
    similars_users_artists.drop(user_listen.columns,axis=1, inplace=True, errors='ignore')

    # Recommended artists
    df_artists_scores = recommended_artists(similars_users_artists, similars_users)

    # Get artists and keep only name and id
    df_artists = pd.read_csv('artists.dat', sep="\t", usecols=['id', 'name'])

    # Join artists and recommended
    df_res = df_artists.merge(df_artists_scores, left_on='id', right_on='artistID')[['id', 'name', 'score']]

    print(df_res.head(10))

get_artists_to_listen_by_user(965)