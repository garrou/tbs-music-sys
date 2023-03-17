import pandas as pd
import tkinter as tk
from tkinter import messagebox
import webbrowser

class App(tk.Tk):
    
    def __init__(self, height, width):
        super().__init__()
        self.title('Artists recommender')
        self.resizable(width=False, height=False)
        
        self.canvas = tk.Canvas(self, height=height, width=width)
        self.canvas.pack()

        self.frame = tk.Frame(self, bg='#080808', bd=5)
        self.frame.place(relx=0.5, rely=0.05, relwidth=0.75, relheight=0.2, anchor='n')

        self.title = tk.Label(self.frame, font=15, bg='#FFFFFF')
        self.title.place(relx=0.1, rely=0.1, relwidth=0.8, relheight=0.4)
        self.title['text'] = 'Enter a user id (from 2 to 2100)'

        self.entry = tk.Entry(self.frame, font=40)
        self.entry.place(relx=0.1, rely=0.6, relwidth=0.5, relheight=0.5)

        self.button = tk.Button(self.frame, text="Launch", bg='#FFFFFF', font=40, command=lambda: self.check_users_and_get(self.entry.get()))
        self.button.place(relx=0.7, rely=0.6, relheight=0.5, relwidth=0.2)

        self.lower_frame = tk.Frame(self, bg='#080808', bd=10)
        self.lower_frame.place(relx=0.5, rely=0.25, relwidth=0.75, relheight=0.70, anchor='n')

        self.listbox = tk.Listbox(self.lower_frame, font=40, bg='#FFFFFF') 
        self.listbox.place(relwidth=1, relheight=0.9)
        self.listbox.bind('<<ListboxSelect>>', self.launch_browser)

        self.label = tk.Label(self.lower_frame, font=15, bg='#FFFFFF')
        self.label.place(rely=0.9, relwidth=1, relheight=0.1)

        self.artists_urls = {}

    def extract_users_artists(self, path_data: str, min_weight: int) -> pd.DataFrame:

        df = pd.read_csv(path_data, sep="\t")

        # Keep weight greater than 100
        return df[df['weight'] > min_weight]

    def create_normalized_matrix(self, df: pd.DataFrame) -> pd.DataFrame:

        # Create a matrix user artist weight
        matrix = pd.pivot_table(df, index='userID', columns='artistID', values = 'weight', aggfunc=sum)
        
        # Normalize matrix
        return matrix.apply(lambda x: x / float(x.sum()))

    def recommended_artists(self, df_similars_users_artists: pd.DataFrame, df_similars_users: pd.DataFrame) -> dict[int, int]:

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

                # If the artist has weight
                if pd.isna(artist_weight[u]) == False:
                    # Score is the sum of user similarity score multiply by the artist weight
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

    def get_artists_to_listen(self, user_id: int) -> pd.DataFrame:
    
        ua_df = self.extract_users_artists('users_artists.dat', 100)

        matrix_norm = self.create_normalized_matrix(ua_df)

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
        df_artists_scores = self.recommended_artists(similars_users_artists, similars_users)

        # Get artists and keep only name and id
        df_artists = pd.read_csv('artists.dat', sep="\t", usecols=['id', 'name', 'url'])

        # Join artists and recommended
        df_res = df_artists.merge(df_artists_scores, left_on='id', right_on='artistID')

        return df_res[['id', 'name', 'url']]

    def generate_list(self, df: pd.DataFrame) -> None:

        self.artists_urls = {}

        for artist in df.values:
            self.artists_urls[artist[1]] = artist[2]
            self.listbox.insert(artist[0], artist[1]) 

    def launch_browser(self, event) -> None:
        selection = event.widget.curselection()
        
        if selection:
            name = event.widget.get(selection[0]) 
            url = self.artists_urls[name]
            webbrowser.open(url)

    def check_users_and_get(self, user_id: str) -> None:

        try:
            df_users_artists = self.extract_users_artists('users_artists.dat', 100)
            user_id = int(user_id)

            if not df_users_artists[df_users_artists['userID'] == user_id].empty:
                self.clear()
                res = self.get_artists_to_listen(user_id)
                self.generate_list(res)
                self.label['text'] = 'Click on artist to open web page'
                tk.messagebox.showinfo(title="Completed", message="Completed recommendations")
            else:
                tk.messagebox.showerror(title="Error", message="This user not exists")
        except Exception as e:
            tk.messagebox.showerror(title="Error", message="Error during computing")

    def clear(self):
        self.listbox.delete(0, tk.END)
        self.label['text'] = ''

App(600, 800).mainloop()