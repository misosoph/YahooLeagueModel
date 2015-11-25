library('ggplot2');
library('Hmisc');
library('data.table');
library('XML');

loadStats <- function(file){
  stats <- data.table(read.csv(file,  header=T, sep=',', dec='.' ))[Rk!='Rk']
  stats[,names(stats)[c(4,6:30)]:=lapply(.SD, function(x) as.numeric(as.character(x))), .SDcols=names(stats)[c(4,6:30)]]
}

dataDir = 'D:/Downloads'#'/Users/jleong/Downloads'
stats2014 <- loadStats(paste(dataDir, '/leagues_NBA_2014_totals_totals.csv', sep=''))
stats2014 <- loadStats(paste(dataDir, '/leagues_NBA_2015_totals_totals.csv', sep=''))
stats2014 <- loadStats(paste(dataDir, '/leagues_NBA_2016_totals_totals.csv', sep=''))

stats <- rbind(stats2014, stats2015, stats2016)
stats <- stats2016

computeRanks <- function(stats){
  statsPerPlayer = stats[Tm!='TOT' & G>4, .(G=sum(G), Age=max(Age), MPG=sum(MP)/sum(G), FG.=weighted.mean(FG.,G),FT.=weighted.mean(FT.,G), FGA=sum(FGA)/sum(G),FTA=sum(FTA)/sum(G),X3P=sum(X3P)/sum(G),PTS=sum(PTS)/sum(G),TRB=sum(TRB)/sum(G),AST=sum(AST)/sum(G),STL=sum(STL)/sum(G),BLK=sum(BLK)/sum(G),TOV=sum(TOV)/sum(G)), keyby=.(Player)]
  #max = sapply(statsPerPlayer[,.(FG.,FT., X3P,PTS,TRB,AST,STL,BLK,TOV)], function(x) max(x, na.rm=T))
  mean = sapply(statsPerPlayer[,.(FG.,FGA,FT.,FTA, X3P,PTS,TRB,AST,STL,BLK,TOV)], function(x) mean(x, na.rm=T))
  sdev = sapply(statsPerPlayer[,.(FG.,FGA,FT.,FTA, X3P,PTS,TRB,AST,STL,BLK,TOV)], function(x) sd(x, na.rm=T))#max-mean
  rankPerPlayer = statsPerPlayer[,.(Player, G, MPG, Age,
                                    FG.=sqrt(FGA/mean['FGA'])*(FG.-mean['FG.'])/sdev['FG.'],
                                    FT.=sqrt(FTA/mean['FTA'])*(FT.-mean['FT.'])/sdev['FT.'],
                                    X3P=(X3P-mean['X3P'])/sdev['X3P'],
                                    PTS=(PTS-mean['PTS'])/sdev['PTS'],
                                    TRB=(TRB-mean['TRB'])/sdev['TRB'],
                                    AST=(AST-mean['AST'])/sdev['AST'],
                                    STL=(STL-mean['STL'])/sdev['STL'],
                                    BLK=(BLK-mean['BLK'])/sdev['BLK'],
                                    TOV=-(TOV-mean['TOV'])/sdev['TOV'])][,score:=(FG.+FT.+X3P+1.1*PTS+1.1*TRB+1.1*AST+STL+BLK+TOV)][,rank:=rank(-score)]
  setcolorder(rankPerPlayer, c('rank', names(rankPerPlayer)[1:(length(rankPerPlayer)-1)]))
  setkey(rankPerPlayer, rank)
  rankPerPlayer
}


computeRanksPerMin <- function(stats){
  pctCols = c('FG.','FT.')
  numCols = c('FGA','FTA','X3P','PTS','TRB','AST','STL','BLK','TOV')
  statsPerPlayer = stats[Tm!='TOT' & G>2, .(G=sum(G), MP=sum(MP), MPG=sum(MP)/sum(G), Age=max(Age), 
                                            FG.=weighted.mean(FG.,MP),
                                            FT.=weighted.mean(FT.,MP), 
                                            FGA=sum(FGA)/sum(MP),
                                            FTA=sum(FTA)/sum(MP),
                                            X3P=sum(X3P)/sum(MP),
                                            PTS=sum(PTS)/sum(MP),
                                            TRB=sum(TRB)/sum(MP),
                                            AST=sum(AST)/sum(MP),
                                            STL=sum(STL)/sum(MP),
                                            BLK=sum(BLK)/sum(MP),
                                            TOV=sum(TOV)/sum(MP)), keyby=.(Player)]
  #max = sapply(statsPerPlayer[,.(FG.,FT., X3P,PTS,TRB,AST,STL,BLK,TOV)], function(x) max(x, na.rm=T))
  mean = sapply(statsPerPlayer[,.(FG.,FGA,FT.,FTA, X3P,PTS,TRB,AST,STL,BLK,TOV)], function(x) mean(x, na.rm=T))
  sdev = sapply(statsPerPlayer[,.(FG.,FGA,FT.,FTA, X3P,PTS,TRB,AST,STL,BLK,TOV)], function(x) sd(x, na.rm=T))#max-mean
  rankPerPlayer = statsPerPlayer[,.(Player, G, MPG, Age, 
                                    FG.=sqrt(FGA/mean['FGA'])*(FG.-mean['FG.'])/sdev['FG.'],
                                    FT.=sqrt(FTA/mean['FTA'])*(FT.-mean['FT.'])/sdev['FT.'],
                                    X3P=(X3P-mean['X3P'])/sdev['X3P'],
                                    PTS=(PTS-mean['PTS'])/sdev['PTS'],
                                    TRB=(TRB-mean['TRB'])/sdev['TRB'],
                                    AST=(AST-mean['AST'])/sdev['AST'],
                                    STL=(STL-mean['STL'])/sdev['STL'],
                                    BLK=(BLK-mean['BLK'])/sdev['BLK'],
                                    TOV=-(TOV-mean['TOV'])/sdev['TOV'])][,score:=(FG.+FT.+X3P+1.1*PTS+1.1*TRB+1.1*AST+STL+BLK+TOV)][,rank:=rank(-score)]
  setcolorder(rankPerPlayer, c('rank', names(rankPerPlayer)[1:(length(rankPerPlayer)-1)]))
  setkey(rankPerPlayer, rank)
  rankPerPlayer
}

ranks2014<-computeRanks(stats2014)
ranks2015<-computeRanks(stats2015)
ranks2016<-computeRanks(stats2016)
ranksPerMin2016<-computeRanksPerMin(stats2016)

ranks <- rbind(ranks2014[,weight:=.5], ranks2015[,weight:=1], ranks2016[,weight:=30])[,.(
  G=sum(G), MPG=weighted.mean(MPG,weight*G, na.rm = T), Age=max(Age), 
  FG.=weighted.mean(FG.,weight*G, na.rm = T),
  FT.=weighted.mean(FT.,weight*G, na.rm = T),
  X3P=weighted.mean(X3P,weight*G, na.rm = T),
  PTS=weighted.mean(PTS,weight*G, na.rm = T),
  TRB=weighted.mean(TRB,weight*G, na.rm = T),
  AST=weighted.mean(AST,weight*G, na.rm = T),
  STL=weighted.mean(STL,weight*G, na.rm = T),
  BLK=weighted.mean(BLK,weight*G, na.rm = T),
  TOV=weighted.mean(TOV,weight*G, na.rm = T),
  score=weighted.mean(score,weight*G, na.rm = T)),keyby=Player][,rank:=rank(-score)]
setcolorder(ranks, c('rank', names(ranks)[1:(length(ranks)-1)]))
#statsPct = stats2014[,.(Player, Pos, Tm, FG.,FT.,)]
#statsNum = stats2014[,.(Player, Pos, Tm, G, X3P,PTS,TRB,AST,STL,BLK,TOV)]
#statsPerPlayer

#melted <- melt(stats2014, id=1:8)

ggplot(melt(ranks2016, id=c(1:3)))+stat_bin(aes(value))+facet_wrap(~variable, scales = 'free')

rosters <- xmlRoot(xmlTreeParse(paste(dataDir,'/LeagueRosters.xml', sep='')))
rosterDt = xmlApply(rosters[['results']], function(team) xmlSApply(team[['roster']][['players']], function(player) xmlValue(player[['name']][['full']])))
names = xmlSApply(rosters[['results']], function(team) xmlValue(team[['name']]))
names(rosterDt)<-names
rosterDt = data.table(melt(rosterDt));
setnames(rosterDt, c('Player','Team'))
setkey(rosterDt, Player)
setkey(ranks, Player)
teamStats = rosterDt[ranks]
#setkey(ranksPerMin2016, Player)
#ranksPerMin2016 = rosterDt[ranksPerMin2016]

rosterDt[,hasPlayer:=Player %in% ranks[,Player]]

#melteam = 'Lin|Teague|Wade|Paul George|Dirk|Carmelo|Bogut|Clarkson|Conley|Kanter|Covington|Markieff Morris';

#teamRanks = ranks2016[Player %like%  team];
teamRank = teamStats[, 
          .(Num=.N,
            FG.=mean(FG., na.rm=T), 
            FT.=mean(FT., na.rm=T),
            X3P=mean(X3P, na.rm=T),
            PTS=mean(PTS, na.rm=T),
            TRB=mean(TRB, na.rm=T),
            AST=mean(AST, na.rm=T),
            STL=mean(STL, na.rm=T),
            BLK=mean(BLK, na.rm=T),
            TOV=mean(TOV, na.rm=T)), keyby=Team][,rank:=sum(FG.,FT.,X3P,PTS,TRB,AST,STL,BLK,TOV), keyby=Team]

available = teamStats[is.na(Team)]
setkey(available, rank)


ggplot(melt(ranks2016, id=c(1:3)))+stat_bin(aes(value))+facet_wrap(~variable, scales = 'free')
