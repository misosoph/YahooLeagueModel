#%% init
import pandas as pd
import numpy as np
import json
from yahoo_oauth import OAuth2
oauth = OAuth2(None, None, from_file='oauth.json')
if not oauth.token_is_valid():
    oauth.refresh_access_token()
from fantasy_sport import FantasySport
yfs = FantasySport(oauth, fmt='json')
oauth.oauth.base_url='https://fantasysports.yahooapis.com/fantasy/v2/'
#%%

#response = json.loads(yfs.get_leagues_teams(['353.l.38761']).content)
league_string = '380.l.9492413'
#league_string = '380.l.171315'
#league_string = '371.l.72059'#
#league_string = '359.l.698246'
ffl_dir = 'D:/workspace/yahoo-ffl'
#%%
response = json.loads(yfs.get_leagues_teams([league_string]).content)
teamnames = [x['team'][0][2]['name'] for k,x in response['fantasy_content']['leagues']['0']['league'][1]['teams'].items() if k not in ['count']]
teamkeys = [x['team'][0][0]['team_key'] for k,x in response['fantasy_content']['leagues']['0']['league'][1]['teams'].items() if k not in ['count']]
#%%

playersByKey = {}
for start in range(1,2000,25):
    response = json.loads(yfs._get('leagues;league_keys='+league_string+'/players;start='+str(start)+"/stats").content)
    players = response['fantasy_content']['leagues']['0']['league'][1]['players']
    if(not players):
        break
    playersByKey.update({x['player'][0][0]['player_key']:{next(iter(d.keys())):next(iter(d.values())) for d in x['player'][0] if isinstance(d, dict)} for k,x in players.items() if k not in ['count']})
#%%
playerFrame = pd.DataFrame.from_dict(playersByKey, orient='index')
playerFrame['name'] = playerFrame.apply(lambda x:x['name']['full'], axis=1)
playerFrame['eligible_positions'] = playerFrame.apply(lambda x:[str(next(iter(d.values()))) for d in x['eligible_positions']], axis=1)
playerFrame['bye_weeks'] = playerFrame.apply(lambda x:next(iter(x['bye_weeks'].values())), axis=1)
#%%

playerStats = pd.concat ([pd.read_csv(ffl_dir + "/stats-2019.csv").assign(year=2019),
pd.read_csv(ffl_dir + "/stats-2018.csv").assign(year=2018),
pd.read_csv(ffl_dir + "/stats-2017.csv").assign(year=2017)])
#playerStats['pos'] = playerStats['position'].apply(lambda x:x[x.find(' - ')+3:])
playerStats.groupby('name').points.mean()
playerStats.set_index('name')
#playerStats['avgPts'] = playerStats['points']/playerStats['games']
#%%
json.loads(yfs._get('leagues;league_keys='+league_string+'/players;count=1').content)['fantasy_content']['leagues']['0']['league']

league_settings = json.loads(oauth.session.get('leagues;league_keys='+league_string+'/settings', params={'format': 'json'}).content)['fantasy_content']['leagues']['0']['league'][1]['settings'][0]
roster_positions = pd.DataFrame([x['roster_position'] for x in league_settings['roster_positions']])
stat_settings = pd.DataFrame([x['stat'] for x in league_settings['stat_categories']['stats']])
stat_settings = pd.merge(stat_settings, pd.DataFrame([x['stat'] for x in league_settings['stat_modifiers']['stats']]), on='stat_id')


#%%
response = json.loads(yfs._get('leagues;league_keys='+league_string+'/draftresults').content)
response = response['fantasy_content']['leagues']['0']['league'][1]['draft_results']
draftresults = pd.DataFrame([x['draft_result'] for k,x in response.items() if k not in ['count'] and 'player_key' in x['draft_result']])
draftresults.assign(name=playerFrame.loc[draftresults.player_key].name.reset_index(drop=True))

#%%
response = json.loads(yfs.get_teams_roster(teamkeys).content)
teams = {team['team'][0][2]['name']:[player['player'][0][2]['name']['full'] 
              for p,player in team['team'][1]['roster']['0']['players'].items() if p not in ['count']] 
              for t,team in response['fantasy_content']['teams'].items() if t not in ['count']}

#%%


