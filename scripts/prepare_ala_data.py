import pandas as pd, numpy as np, json, math, os
import pathlib; ROOT=pathlib.Path(__file__).resolve().parents[1]; A=str(ROOT/'data'/'ala'/'raw_download')+'/'; D=str(ROOT/'data'/'ala')+'/'; os.makedirs(D,exist_ok=True)
G10=['Birds','Plants','Insects','Mammals','Fungi','Reptiles','Amphibians','Fishes','Molluscs','Crustaceans']
MO=['January','February','March','April','May','June','July','August','September','October','November','December']
def cells(df):
    df=df[df.cell.str.contains(',',na=False)].copy(); ll=df.cell.str.split(',',expand=True).astype(float)
    df['lat']=ll[0]; df['lon']=ll[1]; return df
def ring(lat,lon): return [[lon-0.5,lat-0.5],[lon-0.5,lat+0.5],[lon+0.5,lat+0.5],[lon+0.5,lat-0.5],[lon-0.5,lat-0.5]]
R=6371.0088
def area(lat): return R*R*math.radians(1)*abs(math.sin(math.radians(lat+0.5))-math.sin(math.radians(lat-0.5)))
# 1 public sightings per year
y=pd.read_csv(A+'year_by_group.csv'); h=y[(y.records_type=='human observations')&(y.group.isin(G10))&(y.year.between(1990,2024))].copy()
h['layer']=h.group.where(h.group.isin(['Birds','Plants','Insects','Mammals','Fungi']),'Other animals')
h.groupby(['layer','year']).records.sum().reset_index().to_csv(D+'public_sightings_by_year.csv',index=False)
# 2 sources x groups
r=pd.read_csv(A+'resource_by_group.csv'); g=pd.read_csv(A+'groups.csv').set_index('group')
SRC=[('eBird Australia','eBird','Volunteer app'),('iNaturalist Australia','iNaturalist','Volunteer app'),('BirdLife Australia, Birdata','BirdLife Birdata','Volunteer app'),
     ('NatureMapr','NatureMapr','Volunteer app'),('NSW BioNet Atlas','NSW BioNet Atlas','State government atlas'),('Victorian Biodiversity Atlas','Victorian Biodiversity Atlas','State government atlas'),
     ('SA Fauna','SA Fauna','State government atlas'),('Fauna Atlas N.T.','NT Fauna Atlas','State government atlas')]
rows=[]
for grp in G10:
    den=int(g.loc[grp,'human_observations_2016_2025']); sub=r[r.group==grp].set_index('data_resource').records; used=0
    for full,short,typ in SRC:
        n=int(sub.get(full,0)); used+=n; rows.append([short,typ,grp,n,round(n/den*100,1),den])
    rows.append(['All other sources','Other',grp,den-used,round((den-used)/den*100,1),den])
pd.DataFrame(rows,columns=['source','type','group','records','share','group_total']).to_csv(D+'sources_by_group.csv',index=False)
# 3 density grid
gr=cells(pd.read_csv(A+'grid1_by_group.csv')); gr=gr[gr.group.isin(G10+['All wildlife'])]
gr=gr[(gr.lon>=112)&(gr.lon<=155)&(gr.lat>=-44.5)&(gr.lat<=-9)]
feats=[]
for (lat,lon),sub in gr.groupby(['lat','lon']):
    a=area(lat); props={'cell':f"{abs(lat):.0f}°S, {lon:.0f}°E",'area':round(a)}
    for _,rw in sub.iterrows(): props[rw.group]=round(rw.records/a*1000,2); props['n_'+rw.group]=int(rw.records)
    feats.append({"type":"Feature","properties":props,"geometry":{"type":"Polygon","coordinates":[ring(lat,lon)]}})
json.dump({"type":"FeatureCollection","features":feats},open(D+'grid1_density.geojson','w'),separators=(',',':'))
allc=[f['properties'] for f in feats if 'All wildlife' in f['properties']]
print('cells',len(feats),'top',[(p['cell'],p['All wildlife'],p['n_All wildlife']) for p in sorted(allc,key=lambda p:-p['All wildlife'])[:4]])
for grp in ['All wildlife','Birds','Insects','Fungi','Mammals','Crustaceans']:
    v=np.array([f['properties'][grp] for f in feats if grp in f['properties']]); print(grp,len(v),np.percentile(v,[20,40,60,80]).round(2))
# 4 states
pop={"New South Wales":8339000,"Victoria":6812000,"Queensland":5459000,"South Australia":1852000,"Western Australia":2879000,"Tasmania":573000,"Northern Territory":252000,"Australian Capital Territory":467000}
code={"New South Wales":"NSW","Victoria":"Vic.","Queensland":"Qld","South Australia":"SA","Western Australia":"WA","Tasmania":"Tas.","Northern Territory":"NT","Australian Capital Territory":"ACT"}
anchor={"NSW":(146.6,-32.4),"Vic.":(143.4,-36.9),"Qld":(144.6,-23.0),"SA":(135.2,-29.8),"WA":(122.4,-26.0),"Tas.":(149.6,-42.4),"NT":(133.4,-19.6),"ACT":(153.6,-36.6)}
s=pd.read_csv(A+'state_by_group.csv'); s=s[(s.group=='All wildlife')&(s.state.isin(pop))].copy()
s['state_code']=s.state.map(code); s['population']=s.state.map(pop)
s['per_100k_year']=(s.records/10/s.population*1e5).round(0).astype(int)
s['record_share']=(s.records/s.records.sum()*100).round(1); s['pop_share']=(s.population/s.population.sum()*100).round(1)
s['diff']=(s.record_share-s.pop_share).round(1)
s['label_lon']=s.state_code.map(lambda k:anchor[k][0]); s['label_lat']=s.state_code.map(lambda k:anchor[k][1])
s.rename(columns={'state':'name'}).drop(columns='group').to_csv(D+'states_all_wildlife.csv',index=False)
print(s[['state_code','records','per_100k_year','record_share','pop_share','diff']].to_string())
# 5 months by group
m=pd.read_csv(A+'month_by_group.csv'); m=m[m.month!='Not supplied'].copy(); m['m']=m.month.map({k:i+1 for i,k in enumerate(MO)})
m['share']=m.records/m.groupby('group').records.transform('sum')*100
base=m[m.group=='All wildlife'].set_index('m').share
mg=m[m.group.isin(G10)].copy(); mg['all_share']=mg.m.map(base).round(2); mg['share']=mg.share.round(2)
pk=mg.loc[mg.groupby('group').share.idxmax()].set_index('group').m; mg['peak']=mg.group.map(pk)
mg.to_csv(D+'months_by_group.csv',index=False); print(pk.sort_values().to_dict())
# 6 latitude x month
gm=cells(pd.read_csv(A+'grid1_by_month.csv')); gm=gm[gm.month!='Not supplied']
gm=gm[(gm.lon>=112)&(gm.lon<=155)&(gm.lat>=-44)&(gm.lat<=-10)].copy(); gm['m']=gm.month.map({k:i+1 for i,k in enumerate(MO)})
gm['band']=(np.floor((gm.lat+0.5)/2)*2).astype(int)
lb=gm.groupby(['band','m']).records.sum().reset_index()
lb['share']=(lb.records/lb.groupby('band').records.transform('sum')*100).round(2); lb['band_total']=lb.groupby('band').records.transform('sum')
lb['label']=lb.band.apply(lambda b:f"{abs(b+2)}–{abs(b)}°S"); lb.to_csv(D+'latitude_month.csv',index=False)
print(lb.pivot(index='label',columns='m',values='share').round(0).to_string()); print(lb.groupby('label').band_total.first().sort_values().head(4).to_dict())
# 7 seasonal index
gm['cell_total']=gm.groupby('cell').records.transform('sum'); sm=gm[gm.cell_total>=2000].copy()
sm['index']=(sm.records/sm.cell_total*12).round(2); sm['key']=sm.cell+'|'+sm.m.astype(str)
sm[['key','m','records','index']].to_csv(D+'cell_month_index.csv',index=False)
feats=[{"type":"Feature","properties":{"cell":rw.cell,"name":f"{abs(rw.lat):.0f}°S, {rw.lon:.0f}°E","total":int(rw.cell_total)},
        "geometry":{"type":"Polygon","coordinates":[ring(rw.lat,rw.lon)]}} for _,rw in sm.drop_duplicates('cell').iterrows()]
json.dump({"type":"FeatureCollection","features":feats},open(D+'season_cells.geojson','w'),separators=(',',':'))
print('season cells',len(feats),'rows',len(sm))
for mm in (1,3,5,7,10,12):
    q=sm[sm.m==mm]; print(mm,'north >-20:',q[q.lat>-20]['index'].median(),'south <-30:',q[q.lat<-30]['index'].median())
