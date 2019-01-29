import sys
import csv
import pulp
import pandas as pd
from tqdm import tqdm

#USER PARAMETERS
num_lineups = 150
overlap = 4
solver = pulp.CPLEX_PY(msg=0)
# solver = pulp.GLPK(msg=0)
players_filepath = './players.csv'
goalies_filepath = './goalies.csv'
output_filepath = './test_output.csv'

class Optimizer:
	"""Optimizer Class"""
	def __init__(self, num_lineups, overlap, solver, players_filepath, goalies_filepath, output_filepath):
		self.num_lineups = num_lineups
		self.overlap = overlap
		self.solver = solver
		self.skaters_df = pd.read_csv(players_filepath)
		self.goalies_df = pd.read_csv(goalies_filepath)
		self.output_filepath = output_filepath
		self.salary_cap = 50000
		self.max_players = 9

	def type_1(self, lineups, positions, team_lines, skaters_teams, goalies_opponents, num_skaters, num_goalies, num_teams, num_lines):
		""" 
		Sets up the pulp LP problem, adds all of the constraints and solves for the maximum value for each generated lineup.

		Type 1 constraints include:
			- 3-2 stacking (1 line of 3 players and one seperate line of 2 players)
			- goalies stacking
			- team stacking

		Returns a single lineup (i.e all of the players either set to 0 or 1) indicating if a player was included in a lineup or not.
		"""
		#define the pulp object problem
		prob = pulp.LpProblem('NHL', pulp.LpMaximize)

		#define the player and goalie variables
		skaters_lineup = [pulp.LpVariable("player_{}".format(i+1), cat="Binary") for i in range(num_skaters)]
		goalies_lineup = [pulp.LpVariable("goalie_{}".format(i+1), cat="Binary") for i in range(num_goalies)]
		
		#add the max player constraints
		prob += (sum(skaters_lineup[i] for i in range(num_skaters)) == 8)
		prob += (sum(goalies_lineup[i] for i in range(num_goalies)) == 1)

		#add the positional constraints
		prob += (2 <= sum(positions['C'][i]*skaters_lineup[i] for i in range(num_skaters)))
		prob += (sum(positions['C'][i]*skaters_lineup[i] for i in range(num_skaters)) <= 3)
		prob += (3 <= sum(positions['W'][i]*skaters_lineup[i] for i in range(num_skaters)))
		prob += (sum(positions['W'][i]*skaters_lineup[i] for i in range(num_skaters)) <= 4)
		prob += (2 <= sum(positions['D'][i]*skaters_lineup[i] for i in range(num_skaters)))
		prob += (sum(positions['D'][i]*skaters_lineup[i] for i in range(num_skaters)) <= 3)

		#add the salary constraint
		prob += ((sum(self.skaters_df.loc[i, 'sal']*skaters_lineup[i] for i in range(num_skaters)) +
					sum(self.goalies_df.loc[i, 'sal']*goalies_lineup[i] for i in range(num_goalies))) <= self.salary_cap)
		
		#exactly 3 teams for the 8 skaters constraint
		used_team = [pulp.LpVariable("u{}".format(i+1), cat="Binary") for i in range(num_teams)]
		for i in range(num_teams):
			prob += (used_team[i] <= sum(skaters_teams[k][i]*skaters_lineup[k] for k in range(num_skaters)))
			prob += (sum(skaters_teams[k][i]*skaters_lineup[k] for k in range(num_skaters)) <= 6*used_team[i])
		prob += (sum(used_team[i] for i in range(num_teams)) >= 3)

		#no goalies against skaters constraint
		for i in range(num_goalies):
			prob += (6*goalies_lineup[i] + sum(goalies_opponents[k][i]*skaters_lineup[k] for k in range(num_skaters)) <= 6)

		#Must have at least one complete line in each lineup
		line_stack_3 = [pulp.LpVariable("ls3{}".format(i+1), cat="Binary") for i in range(num_lines)]
		for i in range(num_lines):
			prob += (3*line_stack_3[i] <= sum(team_lines[k][i]*skaters_lineup[k] for k in range(num_skaters)))
		prob += (sum(line_stack_3[i] for i in range(num_lines)) >= 1)
		
		#Must have at least 2 lines with at least 2 players
		line_stack_2 = [pulp.LpVariable("ls2{}".format(i+1), cat="Binary") for i in range(num_lines)]
		for i in range(num_lines):
			prob += (2*line_stack_2[i] <= sum(team_lines[k][i]*skaters_lineup[k] for k in range(num_skaters)))
		prob += (sum(line_stack_2[i] for i in range(num_lines)) >= 2)

		#variance constraints - each lineup can't have more than the num overlap of any combination of players in any previous lineups
		for i in range(len(lineups)):
			prob += ((sum(lineups[i][k]*skaters_lineup[k] for k in range(num_skaters)) +
						sum(lineups[i][num_skaters+k]*goalies_lineup[k] for k in range(num_goalies))) <= self.overlap)
		
		#add the objective
		prob += pulp.lpSum((sum(self.skaters_df.loc[i, 'proj']*skaters_lineup[i] for i in range(num_skaters)) +
							sum(self.goalies_df.loc[i, 'proj']*goalies_lineup[i] for i in range(num_goalies))))

		#solve the problem
		status = prob.solve(self.solver)

		#check if the optimizer found an optimal solution
		if status != pulp.LpStatusOptimal:
			print(f'Only {len(lineups)} feasible lineups produced', '\n')
			return None

		# Puts the output of one lineup into a format that will be used later
		lineup_copy = []
		for i in range(num_skaters):
			if skaters_lineup[i].varValue >= 0.9 and skaters_lineup[i].varValue <= 1.1:
				lineup_copy.append(1)
			else:
				lineup_copy.append(0)
		for i in range(num_goalies):
			if goalies_lineup[i].varValue >= 0.9 and goalies_lineup[i].varValue <= 1.1:
				lineup_copy.append(1)
			else:
				lineup_copy.append(0)

		return lineup_copy

	def fill_lineups(self, lineups, positions, num_skaters, num_goalies):
		""" 
		Takes in the lineups with 1's and 0's indicating if the player is used in a lineup.
		Matches the player in the dataframe and replaces the value with their name.
		Saves the filled lineups to a csv file
		"""
		filled_lineups = []
		for lineup in lineups:
			a_lineup = ["", "", "", "", "", "", "", "", ""]
			skaters_lineup = lineup[:num_skaters]
			goalies_lineup = lineup[-1*num_goalies:]
			for num, player in enumerate(skaters_lineup):
				if player == 1:
					if positions['C'][num] == 1:
						if a_lineup[0] == "":
							a_lineup[0] = self.skaters_df.loc[num, 'playerName']
						elif a_lineup[1] == "":
							a_lineup[1] = self.skaters_df.loc[num, 'playerName']
						elif a_lineup[8] == "":
							a_lineup[8] = self.skaters_df.loc[num, 'playerName']
					elif positions['W'][num] == 1:
						if a_lineup[2] == "":
							a_lineup[2] = self.skaters_df.loc[num, 'playerName']
						elif a_lineup[3] == "":
							a_lineup[3] = self.skaters_df.loc[num, 'playerName']
						elif a_lineup[4] == "":
							a_lineup[4] = self.skaters_df.loc[num, 'playerName']
						elif a_lineup[8] == "":
							a_lineup[8] = self.skaters_df.loc[num, 'playerName']
					elif positions['D'][num] == 1:
						if a_lineup[5] == "":
							a_lineup[5] = self.skaters_df.loc[num, 'playerName']
						elif a_lineup[6] == "":
							a_lineup[6] = self.skaters_df.loc[num, 'playerName']
						elif a_lineup[8] == "":
							a_lineup[8] = self.skaters_df.loc[num, 'playerName']
			for num, goalie in enumerate(goalies_lineup):
				if goalie == 1:
					if a_lineup[7] == "":
						a_lineup[7] = self.goalies_df.loc[num, 'playerName']
			filled_lineups.append(a_lineup)
			
		with open(self.output_filepath, 'w') as f:
				writer = csv.writer(f)
				header = ['C', 'C', 'W', 'W', 'W', 'D', 'D', 'G', 'UTIL']
				writer.writerow(header)
				writer.writerows(filled_lineups)

	def create_lineups(self):
		"""
		Set's up the player and team indicators that get used to create the constraints for the pulp problem,
		and generates the max number of lineups in a loop.
		Finishes by calling fill_lineups which converts the lineups to a readable form to output to a csv.
		"""
		num_skaters = len(self.skaters_df.index)
		num_goalies = len(self.goalies_df.index)
		teams = list(set(self.skaters_df['team'].values))
		num_teams = len(teams)

		#Create player position indicators so you know which position they are playing
		positions = {'C':[], 'W':[], 'D':[]}
		for pos in self.skaters_df.loc[:, 'pos']:
			for key in positions:
				positions[key].append(1 if key in pos else 0)
		
		#Create player line indicators so you know which line by their team they are on
		team_lines = []
		for i, line in enumerate(self.skaters_df.loc[:, 'line']):
			player_line = []
			if int(line) == 1:
				player_line.extend((1, 0, 0, 0))
			elif int(line) == 2:
				player_line.extend((0, 1, 0, 0))
			elif int(line) == 3:
				player_line.extend((0, 0, 1, 0))
			elif int(line) == 4:
				player_line.extend((0, 0, 0, 1))
			else:
				player_line.extend((0, 0, 0, 0))
			player_lines = []
			for team in teams:
				if self.skaters_df.loc[i, 'team'] == team:
					player_lines.extend(player_line)
				else:
					player_lines.extend((0, 0, 0, 0))
			team_lines.append(player_lines)
		num_lines = len(team_lines[0])
		
		#NOTE: Maybe add PP line indicators

		#Create player team indicators so you know which team they are on
		skaters_teams = []
		for player_team in self.skaters_df.loc[:, 'team']:
			skaters_teams.append([1 if player_team == team else 0 for team in teams])

		#Create goalie opponent indicators so you know who the goalie is opposing
		goalies_opponents = []
		for player_opp in self.skaters_df.loc[:, 'opp']:
			goalies_opponents.append([1 if player_opp == team else 0 for team in self.goalies_df.loc[:, 'team']])

		#Generate the lineups
		lineups = []
		for _ in tqdm(range(1, self.num_lineups+1)):
			lineup = self.type_1(lineups, positions, team_lines, skaters_teams, goalies_opponents, num_skaters, num_goalies, num_teams, num_lines)
			if lineup:
				lineups.append(lineup)
			else:
				break

		#Fill the lineups with player names
		self.fill_lineups(lineups, positions, num_skaters, num_goalies)

#Set up the Optimizer Class
opp = Optimizer(num_lineups, overlap, solver, players_filepath, goalies_filepath, output_filepath)
#Run the code
opp.create_lineups()
