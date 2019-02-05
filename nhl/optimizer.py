import sys
import csv
import pandas as pd

class Optimizer:
	"""Optimizer Base Class"""
	def __init__(self, players_filepath, goalies_filepath, output_filepath):
		self.skaters_df = pd.read_csv(players_filepath)
		self.goalies_df = pd.read_csv(goalies_filepath)
		self.output_filepath = output_filepath

	def save_file(self, header, filled_lineups):
		with open(self.output_filepath, 'w') as f:
				writer = csv.writer(f)
				writer.writerow(header)
				writer.writerows(filled_lineups)

	def create_indicators(self):
		"""
		Set's up the player and team indicators that get used to create the constraints for the pulp problem,
		Returns the indicators in a tuple.
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

		#return the indicators in a tuple
		return (positions, team_lines, skaters_teams, goalies_opponents, num_skaters, num_goalies, num_teams, num_lines)