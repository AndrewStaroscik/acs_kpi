import pandas as pd
import matplotlib.pyplot as plt


import urllib.request, urllib.error, urllib.parse, json
import lxml

ak = '<enter census api key here>'


# Look up places values by state here: https://www.census.gov/library/reference/code-lists/ansi.html#cousub

# enter target location information: 
munsToGet = [
  {'munVal':'59000', 'stateVal':'44', 'mAbbr':'prov', 'mFull':'Providence', 'sAbbr':'RI'},
  {'munVal':'27425', 'stateVal':'08', 'mAbbr':'ftcol', 'mFull':'Fort Collins', 'sAbbr':'CO'},
  {'munVal':'62535', 'stateVal':'25', 'mAbbr':'somvil', 'mFull':'Somerville', 'sAbbr':'MA'},
  {'munVal':'80700', 'stateVal':'26', 'mAbbr':'troy', 'mFull':'Troy', 'sAbbr':'MI'},
  {'munVal':'73110', 'stateVal':'34', 'mAbbr':'tomsr', 'mFull':'Toms River', 'sAbbr':'NJ'}
]

yearStart = 2013
yearEnd = 2023
yearSkip = 2020
yearList = []
year = yearStart
while year <= yearEnd:
  if year != yearSkip:
    yearList.append(str(year))
  year += 1

acsVarName = 'B25106_'
totalVar = ['B25106_001E']
allCostBurdenedVars = ['B25106_006E', 'B25106_010E', 'B25106_014E', 'B25106_018E', 'B25106_022E', 'B25106_028E', 'B25106_032E', 'B25106_036E', 'B25106_040E', 'B25106_044E']
allZeroCost = ['B25106_023E', 'B25106_046E']
allVars = totalVar + allCostBurdenedVars + allZeroCost

varStr = ''
for el in allVars: 
  varStr += ',' + el


def getData(yL, mun, sta):
	startURL = 'https://api.census.gov/data/'
	midURLa =   '/acs/acs1?get=NAME'
	midURLb = '&for=place:'
	midURLc = '&in=state:'
	endURL = '&key='

	urlList = []
	for el in yL: 
		urlList.append({'y': el, 'url': startURL + el + midURLa + varStr + midURLb + str(mun) + midURLc + str(sta) + endURL +  ak})

	housingBurdenByYear = []

	for el in urlList:
		response = urllib.request.urlopen(el['url']) 
		data = response.read().decode('UTF-8')
		data = json.loads(data) 
		burdenData = pd.DataFrame(data[1:], columns=data[0])
		burdenData['year'] = el['y']
		housingBurdenByYear.append(burdenData)

	data = pd.concat(housingBurdenByYear)

	data.rename(columns={'B25106_001E': 'total'}, inplace=True)
	data['burdened'] = data[allCostBurdenedVars].apply(pd.to_numeric).sum(axis=1)
	data.drop(columns=allCostBurdenedVars, inplace=True)
	data['burdened'] = data['burdened'] - data['B25106_023E'].astype(int) - data['B25106_046E'].astype(int)
	data.drop(columns=allZeroCost, inplace=True)
	data['burdened percent'] = round(100 * data['burdened']/data['total'].astype(int), 2)
	missedYear = data.iloc[-1].copy()
	missedYear['year'] = '2020'
	missedYear['burdened percent'] = 0

	data = pd.concat([data, pd.DataFrame([missedYear])], ignore_index=True)
	data['yearNumber'] = data['year'].astype(int)
	data = data.sort_values(by='yearNumber')

	return data

def makeChart(d, nameAbbr, nameFull, stateAbbr):
	accentColor = '#00EAE7'
	midColor = '#787878'
	axisColor = '#ababab'
	colors = ['#cdcdcd'] * (len(d) - 1) + [accentColor]
	targetVal = round(d.iloc[-1]['burdened percent'],1)
	oneYrDelta = d.iloc[-1]['burdened percent'] - d.iloc[-2]['burdened percent']
	deltaColor = '#565656'
	direct = 'flat'
	arrowIcon = '⟷'
	if oneYrDelta < 0:
		deltaColor = '#005518' 
		direct = 'down'
		arrowIcon = '↓'
	elif oneYrDelta > 0: 
		deltaColor = '#D5002E'
		direct = 'up'
		arrowIcon = '↑'
	else: 
		deltaColor = '#565656'
		direct = 'flat'
		
	colors = ['#cdcdcd'] * (len(d) - 1) + [deltaColor]
		

	fig = plt.figure(figsize=(8,6))

	ax = fig.add_axes([0.1, 0.1, 0.8, 0.425]) # left bottom w, h

	bars = d.plot(ax=ax, x='year', y='burdened percent', kind='bar', color=colors, legend=False)

	fig.text(0.5, 0.9, nameFull + ', ' + stateAbbr, fontsize=30, ha='center', va='center', color=midColor)
	fig.text(0.5, 0.83, 'Housing Cost Burdened Households', fontsize=20, ha='center', va='center', color=midColor)
	fig.text(0.1, 0.75, '2013-2023', fontsize=20, ha='left', va='center', color=axisColor)
	fig.text(0.1, 0.65, str(targetVal) + '%', fontsize=55, ha='left', va='center', color='#343434')
	fig.text(0.1, 0.57, arrowIcon + ' Burdened households ' + direct + ' ' + str(round(abs(oneYrDelta),2)) + '% YoY' , fontsize=18, ha='left', va='center', color=deltaColor)
	fig.text(0.95, 0.03, 'Andrew Staroscik', fontsize=10, ha='right', va='center', color=axisColor)
	fig.text(0.05, 0.03, 'Data: American Community Survey one-year estimates', fontsize=10, ha='left', va='center', color=axisColor)

	plt.xticks(rotation=0)
	ax.spines['top'].set_visible(False)
	ax.spines['right'].set_visible(False)

	ax.spines['bottom'].set_color(axisColor)
	ax.spines['left'].set_color(axisColor)  

	ax.tick_params(axis='x', colors=axisColor)
	ax.tick_params(axis='y', colors=axisColor)
	ax.yaxis.label.set_color(axisColor)

	ax.set_xlabel('')
	ax.set_ylabel('Households (%)')


	for i, bar in enumerate(ax.patches):
		yr = d.iloc[i]['year']
		if i == len(ax.patches) - 1:  # Target the last bar
			x = bar.get_x() + bar.get_width() / 2
			y = bar.get_height()
			ax.text(x, y+ 1.5, f'{y:.1f}%', ha='center', va='bottom', fontsize=16, color='#002B2A')

		if yr == '2020': 
			x = bar.get_x() + bar.get_width() / 2
			y = bar.get_height()
			ax.text(x, 2, 'no data', rotation=90, ha='center', va='bottom', fontsize=12, color=axisColor)
					

	fig.savefig('./images/' + nameAbbr + stateAbbr +  '_Burdened.png', dpi=300)
    
for el in munsToGet: 
	dat = getData(yearList, el['munVal'], el['stateVal'])
	makeChart(dat, el['mAbbr'], el['mFull'], el['sAbbr'])

		