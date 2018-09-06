#%% init
import pandas as pd
import numpy as np
import json
from yahoo_oauth import OAuth2
oauth = OAuth2(None, None, from_file='e:\workspace\yahooleaguemodel\oauth.json')
if not oauth.token_is_valid():
    oauth.refresh_access_token()
from fantasy_sport import FantasySport
yfs = FantasySport(oauth, fmt='json')
oauth.oauth.base_url='https://fantasysports.yahooapis.com/fantasy/v2/'
#%%
#response = json.loads(yfs.get_leagues_teams(['353.l.38761']).content)
#league_string = '364.l.35083'
league_string = '375.l.28302'
response = json.loads(yfs.get_leagues_teams([league_string]).content)
teamnames = [x['team'][0][2]['name'] for k,x in response['fantasy_content']['leagues']['0']['league'][1]['teams'].iteritems() if k not in ['count']]
teamkeys = [x['team'][0][0]['team_key'] for k,x in response['fantasy_content']['leagues']['0']['league'][1]['teams'].iteritems() if k not in ['count']]
#%%
response = json.loads(yfs.get_teams_roster(teamkeys).content)
teams = {team['team'][0][2]['name']:[player['player'][0][2]['name']['full'] for p,player in team['team'][1]['roster']['0']['players'].iteritems() if p not in ['count']] for t,team in response['fantasy_content']['teams'].iteritems() if t not in ['count']}
#%%
response = json.loads(yfs._get('leagues;league_keys='+league_string+'/settings').content)['fantasy_content']['leagues']['0']['league'][1]['settings'][0]['stat_categories']['stats']
stat_names = {v['stat']['stat_id']:v['stat']['display_name'] for v in response}

#%%
playersByKey = {}
playersStats = {}
for start in xrange(1,2000,25):
    response = json.loads(yfs._get('leagues;league_keys='+league_string+'/players;start='+str(start)+"/stats;type=season;season=2016").content)
    playerList = [x['player'] for k,x in response['fantasy_content']['leagues']['0']['league'][1]['players'].iteritems() if k not in ['count']]
    playersByKey.update({x[0][0]['player_key']:{d.keys()[0]:d.values()[0] for d in x[0] if isinstance(d, dict)} for x in playerList})
    for x in playerList:
        playerkey = x[0][0]['player_key']
        playersStats[playerkey] = {}
        for s in x[1]['player_stats']['stats']:
            stat_id = s['stat']['stat_id']
            playersStats[playerkey][stat_names[int(stat_id)]]= s['stat']['value']
            
#%%
playerFrame = pd.DataFrame.from_dict(playersByKey, orient='index')
playerFrame['name'] = playerFrame.apply(lambda x:x['name']['full'], axis=1)
playerFrame['eligible_positions'] = playerFrame.apply(lambda x:[str(d.values()[0]) for d in x['eligible_positions']], axis=1)
#%%
playerStatsFrame = pd.DataFrame.from_dict(playersStats, orient='index')
playerStatsFrame = pd.concat([playerStatsFrame,playerStatsFrame['FTM/A'].str.split('/', expand=True).rename(columns={0:'FTM', 1:'FTA'})], axis=1 )
playerStatsFrame = pd.concat([playerStatsFrame,playerStatsFrame['FGM/A'].str.split('/', expand=True).rename(columns={0:'FGM', 1:'FGA'})], axis=1 )
playerStatsFrame.drop('FTM/A', axis=1, inplace=True)
playerStatsFrame.drop('FGM/A', axis=1, inplace=True)
playerStatsFrame = playerStatsFrame.apply(lambda x: pd.to_numeric(x, errors="coerce"))
playerStatsFrame['name'] = playerFrame.apply(lambda x: x['name'], axis=1)
playerStatsFrame = playerStatsFrame[['name']+playerStatsFrame.columns.tolist()[:-1]]
playerStatsFrame['fantasy_team'] = ''
#playerFrame['bye_weeks'] = playerFrame.apply(lambda x:x['bye_weeks'].values()[0], axis=1)
#%%
playerZScores = playerStatsFrame[playerStatsFrame.columns.tolist()[1:len(playerStatsFrame.columns)-1]].apply(lambda x:(x-x.mean(skipna=True))/x.std(skipna=True))
#%%
for teamname, players in teams.iteritems():
    for player in players:
        playerStatsFrame.loc[playerStatsFrame['name']==player,'fantasy_team']=teamname
#%%
playerStatsFrame.groupby('fantasy_team').sum()
#%%
json.loads(yfs._get('leagues;league_keys='+league_string+'/players;count=1').content)['fantasy_content']['leagues']['0']['league']
json.loads(yfs._get('leagues;league_keys='+league_string+'/settings').content)
json.loads(yfs._get('leagues;league_keys='+league_string+'/draftresults').content)
#%%
response = json.loads(yfs._get('leagues;league_keys='+league_string+'/draftresults').content)
sorted([x['draft_result'] for k,x in response['fantasy_content']['leagues']['0']['league'][1]['draft_results'].iteritems() if k not in ['count'] and 'player_key' in x['draft_result']], key=lambda x:x['pick'])
#%%
print(response)

downloadDir = '/Users/jleong/Downloads'
file = downloadDir + '/leagues_NBA_2016_totals_totals.csv'
stats2016=pd.read_csv(file, header=0)
stats2016= stats2016[(stats2016['Player']!='Player') & (stats2016['Tm']!='Tot')].convert_objects(convert_numeric=True)

def pg(df, column):
    return df[column].sum()/df['G'].sum()

mean2016=stats2016.groupby('Player').apply(lambda x: pd.Series({'Age':x.Age.max(), 'Pos':x.Pos.max(), 'G':x.G.sum(),
                                                                'GS':x.GS.sum(),
                                                                'MP':pg(x,'MP'),
                                                                'TRB':pg(x,'TRB'),
                                                                'FG':pg(x,'FG'),
                                                                'FGA':pg(x,'FGA')
                                                                #       'FG%', '3P', '3PA', '3P.1', '2P', '2PA', '2P.1', 'eFG%', 'FT',
                                                                #       'FTA', 'FT%', 'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF',
                                                                #       'PTS'
                                                                }))