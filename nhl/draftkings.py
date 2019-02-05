import pulp
from nhl.optimizer import Optimizer

class Draftkings(Optimizer):
	"""
	Draftkings Optimizer Settings
	Draftkings will inherit from the super class Optimizer
	"""
	def __init__(self, num_lineups, overlap, solver, players_filepath, goalies_filepath, output_filepath):
		super().__init__(num_lineups, overlap, solver, players_filepath, goalies_filepath, output_filepath)
		self.salary_cap = 50000
		self.header = ['C', 'C', 'W', 'W', 'W', 'D', 'D', 'G', 'UTIL']

	def type_1(self, lineups, positions, team_lines, skaters_teams, goalies_opponents, num_teams, num_lines):
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
		skaters_lineup = [pulp.LpVariable("player_{}".format(i+1), cat="Binary") for i in range(self.num_skaters)]
		goalies_lineup = [pulp.LpVariable("goalie_{}".format(i+1), cat="Binary") for i in range(self.num_goalies)]
		
		#add the max player constraints
		prob += (pulp.lpSum(skaters_lineup[i] for i in range(self.num_skaters)) == 8)
		prob += (pulp.lpSum(goalies_lineup[i] for i in range(self.num_goalies)) == 1)

		#add the positional constraints
		prob += (2 <= pulp.lpSum(positions['C'][i]*skaters_lineup[i] for i in range(self.num_skaters)))
		prob += (pulp.lpSum(positions['C'][i]*skaters_lineup[i] for i in range(self.num_skaters)) <= 3)
		prob += (3 <= pulp.lpSum(positions['W'][i]*skaters_lineup[i] for i in range(self.num_skaters)))
		prob += (pulp.lpSum(positions['W'][i]*skaters_lineup[i] for i in range(self.num_skaters)) <= 4)
		prob += (2 <= pulp.lpSum(positions['D'][i]*skaters_lineup[i] for i in range(self.num_skaters)))
		prob += (pulp.lpSum(positions['D'][i]*skaters_lineup[i] for i in range(self.num_skaters)) <= 3)

		#add the salary constraint
		prob += ((pulp.lpSum(self.skaters_df.loc[i, 'sal']*skaters_lineup[i] for i in range(self.num_skaters)) +
					pulp.lpSum(self.goalies_df.loc[i, 'sal']*goalies_lineup[i] for i in range(self.num_goalies))) <= self.salary_cap)
		
		#exactly 3 teams for the 8 skaters constraint
		used_team = [pulp.LpVariable("u{}".format(i+1), cat="Binary") for i in range(num_teams)]
		for i in range(num_teams):
			prob += (used_team[i] <= pulp.lpSum(skaters_teams[k][i]*skaters_lineup[k] for k in range(self.num_skaters)))
			prob += (pulp.lpSum(skaters_teams[k][i]*skaters_lineup[k] for k in range(self.num_skaters)) <= 6*used_team[i])
		prob += (pulp.lpSum(used_team[i] for i in range(num_teams)) >= 3)

		#no goalies against skaters constraint
		for i in range(self.num_goalies):
			prob += (6*goalies_lineup[i] + pulp.lpSum(goalies_opponents[k][i]*skaters_lineup[k] for k in range(self.num_skaters)) <= 6)

		#Must have at least one complete line in each lineup
		line_stack_3 = [pulp.LpVariable("ls3{}".format(i+1), cat="Binary") for i in range(num_lines)]
		for i in range(num_lines):
			prob += (3*line_stack_3[i] <= pulp.lpSum(team_lines[k][i]*skaters_lineup[k] for k in range(self.num_skaters)))
		prob += (pulp.lpSum(line_stack_3[i] for i in range(num_lines)) >= 1)
		
		#Must have at least 2 lines with at least 2 players
		line_stack_2 = [pulp.LpVariable("ls2{}".format(i+1), cat="Binary") for i in range(num_lines)]
		for i in range(num_lines):
			prob += (2*line_stack_2[i] <= pulp.lpSum(team_lines[k][i]*skaters_lineup[k] for k in range(self.num_skaters)))
		prob += (pulp.lpSum(line_stack_2[i] for i in range(num_lines)) >= 2)

		#variance constraints - each lineup can't have more than the num overlap of any combination of players in any previous lineups
		for i in range(len(lineups)):
			prob += ((pulp.lpSum(lineups[i][k]*skaters_lineup[k] for k in range(self.num_skaters)) +
						pulp.lpSum(lineups[i][self.num_skaters+k]*goalies_lineup[k] for k in range(self.num_goalies))) <= self.overlap)
		
		#add the objective
		prob += pulp.lpSum((pulp.lpSum(self.skaters_df.loc[i, 'proj']*skaters_lineup[i] for i in range(self.num_skaters)) +
							pulp.lpSum(self.goalies_df.loc[i, 'proj']*goalies_lineup[i] for i in range(self.num_goalies))))

		#solve the problem
		status = prob.solve(self.solver)

		#check if the optimizer found an optimal solution
		if status != pulp.LpStatusOptimal:
			print(f'Only {len(lineups)} feasible lineups produced', '\n')
			return None

		# Puts the output of one lineup into a format that will be used later
		lineup_copy = []
		for i in range(self.num_skaters):
			if skaters_lineup[i].varValue >= 0.9 and skaters_lineup[i].varValue <= 1.1:
				lineup_copy.append(1)
			else:
				lineup_copy.append(0)
		for i in range(self.num_goalies):
			if goalies_lineup[i].varValue >= 0.9 and goalies_lineup[i].varValue <= 1.1:
				lineup_copy.append(1)
			else:
				lineup_copy.append(0)
		return lineup_copy

	def fill_lineups(self, lineups, positions):
		""" 
		Takes in the lineups with 1's and 0's indicating if the player is used in a lineup.
		Matches the player in the dataframe and replaces the value with their name.
		"""
		filled_lineups = []
		for lineup in lineups:
			a_lineup = ["", "", "", "", "", "", "", "", ""]
			skaters_lineup = lineup[:self.num_skaters]
			goalies_lineup = lineup[-1*self.num_goalies:]
			for num, player in enumerate(skaters_lineup):
				if player > 0.9 and player < 1.1:
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
				if goalie > 0.9 and goalie < 1.1:
					if a_lineup[7] == "":
						a_lineup[7] = self.goalies_df.loc[num, 'playerName']
			filled_lineups.append(a_lineup)
		return filled_lineups
