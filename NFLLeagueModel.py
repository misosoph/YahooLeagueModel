#%% init
import pandas as pd
import numpy as np
import json
from yahoo_oauth import OAuth1
oauth = OAuth1(None, None, from_file='oauth.json')
if not oauth.token_is_valid():
    oauth.refresh_access_token()
from fantasy_sport import FantasySport
yfs = FantasySport(oauth, fmt='json')

#%%

#response = json.loads(yfs.get_leagues_teams(['353.l.38761']).content)
league_string = '359.l.698246'

response = json.loads(yfs.get_leagues_teams([league_string]).content)
teamnames = [x['team'][0][2]['name'] for k,x in response['fantasy_content']['leagues']['0']['league'][1]['teams'].iteritems() if k not in ['count']]
teamkeys = [x['team'][0][0]['team_key'] for k,x in response['fantasy_content']['leagues']['0']['league'][1]['teams'].iteritems() if k not in ['count']]
#%%
response = json.loads(yfs.get_teams_roster(teamkeys).content)
teams = {team['team'][0][2]['name']:[player['player'][0][2]['name']['full'] for p,player in team['team'][1]['roster']['0']['players'].iteritems() if p not in ['count']] for t,team in response['fantasy_content']['teams'].iteritems() if t not in ['count']}

playersByKey = {}
for start in xrange(1,2000,25):
    playersByKey.update({x['player'][0][0]['player_key']:{d.keys()[0]:d.values()[0] for d in x['player'][0] if isinstance(d, dict)} for k,x in json.loads(yfs._get('leagues;league_keys='+league_string+'/players;start='+str(start)+"/stats").content)['fantasy_content']['leagues']['0']['league'][1]['players'].iteritems() if k not in ['count']})

playerFrame = pd.DataFrame.from_dict(playersByKey, orient='index')
playerFrame['name'] = playerFrame.apply(lambda x:x['name']['full'], axis=1)
playerFrame['eligible_positions'] = playerFrame.apply(lambda x:[str(d.values()[0]) for d in x['eligible_positions']], axis=1)
playerFrame['bye_weeks'] = playerFrame.apply(lambda x:x['bye_weeks'].values()[0], axis=1)

playerStats=pd.read_csv("/Users/jleong/GitHub/yahoo-ffl/stats2016.csv")
playerStats.append(pd.read_csv("/Users/jleong/GitHub/yahoo-ffl/stats2015.csv"))
playerStats.append(pd.read_csv("/Users/jleong/GitHub/yahoo-ffl/stats2014.csv"))
playerStats['pos'] = playerStats['position'].apply(lambda x:x[x.find(' - ')+3:])
playerStats.groupby('name').agg(lambda x:x['points']/x['games'])
playerStats.set_index('name')
playerStats['avgPts'] = playerStats['points']/playerStats['games']

json.loads(yfs._get('leagues;league_keys='+league_string+'/players;count=1').content)['fantasy_content']['leagues']['0']['league']
json.loads(yfs._get('leagues;league_keys='+league_string+'/settings').content)
json.loads(yfs._get('leagues;league_keys='+league_string+'/draftresults').content)
sorted([x['draft_result']['player_key'] for k,x in json.loads(yfs._get('leagues;league_keys='+league_string+'/draftresults').content)['fantasy_content']['leagues']['0']['league'][1]['draft_results'].iteritems() if k not in ['count'] and 'player_key' in x['draft_result']], key=lambda x:x['pick'])
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