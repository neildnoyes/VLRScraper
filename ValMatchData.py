import os
from StatClass import ValStats

# instantiate our class
stat_class = ValStats(event_id='1188', event_name='champions-tour-2023-lock-in-s-o-paulo')

# set flags
read_from_file = False
send_to_csv = True

if read_from_file:
    # read data
    stat_data_frame = stat_class.from_csv_to_df('19Feb2023_stats.csv')
else:
    # scrape & clean data
    stat_data_frame = stat_class.match_stats_from_web_to_df()

if send_to_csv:
    # send dataframe to csv
    stat_data_frame.to_csv(f'{os.getcwd()}\\data\\{stat_class.get_date()}'
                           f'_matches_event_{stat_class.get_event_id()}.csv')
