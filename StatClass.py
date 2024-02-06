import pandas as pd
from bs4 import BeautifulSoup
import requests
from datetime import datetime


class ValStats:

    def __init__(self, event_group_id='all', event_id='all',
                 region='all', country='all',
                 min_rounds=0, min_rating=0,
                 agent='all', map_id='all',
                 timespan='90d', group='completed',
                 series_id='all', event_name='',
                 subseries_id='all'):
        self.CALL_PARAMS['event_group_id'] = event_group_id
        self.CALL_PARAMS['event_id'] = event_id
        self.CALL_PARAMS['region'] = region
        self.CALL_PARAMS['country'] = country
        self.CALL_PARAMS['min_rounds'] = min_rounds
        self.CALL_PARAMS['min_rating'] = min_rating
        self.CALL_PARAMS['agent'] = agent
        self.CALL_PARAMS['map_id'] = map_id
        self.CALL_PARAMS['timespan'] = timespan
        self.CALL_PARAMS['group'] = group
        self.CALL_PARAMS['series_id'] = series_id
        self.CALL_PARAMS['subseries_id'] = subseries_id
        self.CALL_PARAMS['event_name'] = event_name

    # *********************************** constants ***********************************
    CALL_PARAMS = {
                'event_group_id': '',
                'event_id': '',
                'region': '',
                'country': '',
                'min_rounds': 0,
                'min_rating': 0,
                'agent': '',
                'map_id': '',
                'timespan': '',
                'group': '',
                'series_id': '',
                'subseries_id': '',
                'event_name': '',
    }

    # *********************************** helpers ***********************************
    # used to returns the event id for class instance
    def get_event_id(self):
        return self.CALL_PARAMS['event_id']

    # used to input a previously generated and saved .csv file and return a dataframe
    @staticmethod
    def from_csv_to_df(filename):
        return pd.read_csv('data\\' + filename)

    # used to return formatted date string for our .csv filenames
    @staticmethod
    def get_date():
        return datetime.now().strftime("%d%b%Y")

    # used to return the index of whatever score is larger in given score list between index 0 and 1
    @staticmethod
    def return_winner_index(score_list):
        index = ''
        if not score_list:
            index = None

        if score_list[0] > score_list[1]:
            index = 0
        else:
            index = 1

        return index

    # used to return a formatted dataframe, given a beautiful soup doc
    @staticmethod
    def format_player_data(soup_doc):
        # get our headers
        table_head = soup_doc.thead
        headers = []
        for x in table_head.find_all('tr'):
            for y in x.find_all('th'):
                headers.append(y.text)

        # get our body data
        table_body = soup_doc.tbody
        body = []
        for x in table_body.find_all('tr')[0:]:
            td_tags = x.find_all('td')
            images = x.find_all('img')

            td_val = [y.text for y in td_tags]

            # loop agents
            agents_played = ''
            start = '/img/vlr/game/agents/'
            end = '.png'
            for img in images:
                src_text = img['src']
                src_text = src_text[src_text.find(start) + len(start):src_text.rfind(end)]
                agents_played = agents_played + src_text + ' '

            # replace our agent data with our looped img src
            td_val[1] = agents_played

            body.append(td_val)

        # set our column max
        pd.set_option('display.max_columns', None)

        # ********** START CLEANING **********

        # use pandas to put them together into a dataframe
        dataframe = pd.DataFrame(body, columns=headers)

        # remove new lines from Agents column
        dataframe['Agents'] = dataframe['Agents'].str.replace('\n', '')

        # strip Player column
        dataframe['Player'] = dataframe['Player'].str.strip()

        # split Player into Player and Team on the new line
        dataframe[['Player', 'Team']] = dataframe.Player.str.split('\n', expand=True)

        # strip CL column
        dataframe['CL'] = dataframe['CL'].str.strip()

        # strip KMax column
        dataframe['KMax'] = dataframe['KMax'].str.strip()

        # create column for fk - fd
        dataframe['FK'] = pd.to_numeric(dataframe['FK'])
        dataframe['FD'] = pd.to_numeric(dataframe['FD'])
        dataframe['FK - FD'] = dataframe['FK'] - dataframe['FD']

        # make columns numeric
        dataframe['ACS'] = pd.to_numeric(dataframe['ACS'])
        dataframe['K:D'] = pd.to_numeric(dataframe['K:D'])

        return dataframe

    # used to scrape data from the web, format it and return a dataframe
    def player_stats_from_web_to_df(self):
        base_url = 'https://www.vlr.gg/stats/'

        result = requests.get(
            base_url,
            params={
                'event_group_id': self.CALL_PARAMS.get('event_group_id'),
                'event_id': self.CALL_PARAMS.get('event_id'),
                'region': self.CALL_PARAMS.get('region'),
                'country': self.CALL_PARAMS.get('country'),
                'min_rounds': self.CALL_PARAMS.get('min_rounds'),
                'min_rating': self.CALL_PARAMS.get('min_rating'),
                'agent': self.CALL_PARAMS.get('agent'),
                'map_id': self.CALL_PARAMS.get('map_id'),
                'timespan': self.CALL_PARAMS.get('timespan'),
            },
            timeout=30,
            verify=False
        )

        # get our document and force through BS
        doc = BeautifulSoup(result.content, "html.parser")

        # format into dataframe
        data_frame = self.format_player_data(doc)

        return data_frame

    def format_match_data(self, soup_doc):

        # single_matches = soup_doc.find_all("div", attrs={"class": "match-item-vs"})

        #  find all the sections for dates, games for that day, and games themselves
        # dates and match containers are 1-1 relationship,
        # but we have (possibly) many matches in each container...
        # we need to match the date to a container and then for each match in the container,
        # we then add that piece of data (the date) to each match
        # single_matches = soup_doc.find_all("div", attrs={"class": "match-item-vs"})
        dates = []
        dates_divs = soup_doc.find_all("div", attrs={"class": "wf-label mod-large"})
        for each_date in dates_divs:
            dates.append(each_date.text)
        # print(f'Dates: {dates}\n')

        match_containers = soup_doc.find_all("div", attrs={"class": "wf-card"})
        match_containers.pop(0)  # because first value is title info

        # have structure to store data for each game
        COLUMN_NAMES = ['Team 1', 'Team 2', 'Team 1 Score', 'Team 2 Score', 'Winner', 'Date']
        match_df = pd.DataFrame(columns=COLUMN_NAMES)

        # for each match container
        container_counter = 0
        for i in match_containers:

            # we get the list of matches in that container
            match_list_in_container = i.find_all("div", attrs={"class": "match-item-vs"})

            # for each match in the list of matches
            for each_match in match_list_in_container:

                teams_in_match = []
                score_in_match = []

                # find the team name containers (2 for each match)
                team_names = each_match.find_all("div", attrs={"class": "text-of"})

                for each_name in team_names:
                    teams_in_match.append(each_name.text)

                # find the score containers (2 for each match)
                team_scores = each_match.find_all("div", attrs={"class": "match-item-vs-team-score"})

                for each_score in team_scores:
                    score_in_match.append(each_score.text)

                # structure for reference ['Team 1', 'Team 2', 'Team 1 Score', 'Team 2 Score', 'Winner', 'Date']
                match_df.loc[len(match_df)] = [teams_in_match[0], teams_in_match[1],
                                               score_in_match[0], score_in_match[1],
                                               teams_in_match[self.return_winner_index(score_in_match)],
                                               dates[container_counter]]

            # increment container count
            container_counter = container_counter + 1

        # Trim whitespace and tabs from all columns
        match_df = match_df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

        return match_df

    # used to scrape data from the web, format it and return a dataframe
    def match_stats_from_web_to_df(self):
        base_url = 'https://www.vlr.gg/event/matches/'

        result = requests.get(
            base_url + self.CALL_PARAMS.get('event_id') + '/' + self.CALL_PARAMS.get('event_name') + '/',
            params={
                'series_id': self.CALL_PARAMS.get('series_id'),
                'group': self.CALL_PARAMS.get('group'),
            },
            timeout=30,
            verify=False
        )

        print(f'Url used: {result.url} \n')

        # get our document and force through BS
        doc = BeautifulSoup(result.content, "html.parser")

        # format into dataframe
        data_frame = self.format_match_data(doc)

        return data_frame

    # *********************************** stat functions ***********************************
    def create_top_x_acs(self, df, top_x=10):
        # create acs top x
        acs_top_x = df.filter(['Team', 'Player', 'ACS', 'Agents'], axis=1)\
            .sort_values(by=['ACS'], ascending=False).head(top_x)
        acs_top_x.reset_index(inplace=True, drop=True)
        print(acs_top_x)
        print('\n')
        return acs_top_x

    def create_fk_fd_diff(self, df, top_x=10):
        # create first kill difference top 10
        fk_fd_top_x = df.filter(['Team', 'Player', 'FK', 'FD', 'FK - FD', 'Agents'], axis=1)\
            .sort_values(by=['FK - FD'], ascending=False).head(top_x)
        fk_fd_top_x.reset_index(inplace=True, drop=True)
        print(fk_fd_top_x)
        print('\n')
        return fk_fd_top_x

    def create_kd_top_x(self, df, top_x=10):
        # create kd ratio top x
        kd_top_x = df.filter(['Team', 'Player', 'K:D', 'Agents'], axis=1)\
            .sort_values(by=['K:D'], ascending=False).head(top_x)
        kd_top_x.reset_index(inplace=True, drop=True)
        print(kd_top_x)
        print('\n')
        return kd_top_x

    def create_rating_top_x(self, df, top_x=10):
        # create kd ratio top x
        rating_top_x = df.filter(['Team', 'Player', 'R', 'Agents'], axis=1)\
            .sort_values(by=['R'], ascending=False).head(top_x)
        rating_top_x.reset_index(inplace=True, drop=True)
        print(rating_top_x)
        print('\n')
        return rating_top_x

    def create_stats_for_team(self, df, team, top_x=10):
        # create team stats
        team_stats = df.loc[df['Team'] == team].head(top_x)
        print(team_stats)
        print('\n')
        return team_stats

    def team_averages(self, team_df):

        # get number players
        num_players = len(team_df)

        # get first row with team to build our 1 row table for data
        team_avg_df = team_df.filter(['Team']).head(1)

        # get avg acs
        team_avg_df['Avg ACS'] = team_df['ACS'].mean()

        # get avg kd
        # team_avg_df['Avg K:D'] = team_df['K:D'].sum() / num_players

        # get team fk fd diff
        team_avg_df['Team FK-FD'] = team_df['FK - FD'].sum()

        # print
        print(team_avg_df)
