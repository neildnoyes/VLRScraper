import os
from StatClass import ValStats


# *********************************** main ***********************************

# instantiate our class
stat_class = ValStats(event_id='1188', timespan='all')

# set flags
read_from_file = False
send_to_csv = False

if read_from_file:
    # read data
    stat_data_frame = stat_class.from_csv_to_df('03May2023_stats_event_1188.csv')
else:
    # scrape & clean data
    stat_data_frame = stat_class.player_stats_from_web_to_df()

if send_to_csv:
    # send dataframe to csv
    stat_data_frame.to_csv(f'{os.getcwd()}\\data\\{stat_class.get_date()}'
                           f'_players_event_{stat_class.get_event_id()}.csv')

# stats
stat_class.create_top_x_acs(stat_data_frame)
stat_class.create_fk_fd_diff(stat_data_frame)
stat_class.create_kd_top_x(stat_data_frame)
stat_class.create_rating_top_x(stat_data_frame)
