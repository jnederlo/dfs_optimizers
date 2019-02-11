import sys
import csv
import pulp
import pandas as pd
from tqdm import tqdm

class Optimizer:
	"""
	Optimizer Base Class
	"""
	def __init__(self, num_lineups, overlap, solver, players_filepath, goalies_filepath, output_filepath):
		self.num_lineups = num_lineups
		self.overlap = overlap
		self.solver = solver
		self.skaters_df = self.load_inputs(players_filepath)
		self.goalies_df = self.load_inputs(goalies_filepath)
		self.num_skaters = len(self.skaters_df.index)
		self.num_goalies = len(self.goalies_df.index)
		self.output_filepath = output_filepath
		self.positions = {'C':[], 'W':[], 'D':[]}
		self.team_lines = []
		self.skaters_teams = []
		self.goalies_teams = []
		self.goalies_opponents = []
		self.num_teams = None
		self.num_lines = None
		self.actuals = True if 'actual' in self.skaters_df and 'actual' in self.goalies_df else False

	def load_inputs(self, filepath):
		"""
		Returns the loaded data from the user filepath into a pandas dataframe.
		"""
		try:
			data = pd.read_csv(filepath)
		except IOError:
			sys.exit('INVALID FILEPATH: {}'.format(filepath))
		return data

	def save_file(self, header, filled_lineups):
		"""
		Save the filled lineups to a csv.
		"""
		with open(self.output_filepath, 'w') as f:
				writer = csv.writer(f)
				if self.actuals:
					header.extend(('PROJ', 'ACTUAL'))
				writer.writerow(header)
				writer.writerows(filled_lineups)
		print("Saved lineups to: {}".format(self.output_filepath))

	def create_indicators(self):
		"""
		Preprocesses the data and classifies players into different indicators for constraints.
		The indicators are saved as class variables.
		"""
		teams = list(set(self.skaters_df['team'].values))
		self.num_teams = len(teams)

		#Create player position indicators so you know which position they are playing
		for pos in self.skaters_df.loc[:, 'pos']:
			for key in self.positions:
				self.positions[key].append(1 if key in pos else 0)
		
		#Create player line indicators so you know which line by their team they are on
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
			self.team_lines.append(player_lines)
		self.num_lines = len(self.team_lines[0])

		#Create player team indicators so you know which team they are on (for use in DK team constraint)
		for player_team in self.skaters_df.loc[:, 'team']:
			self.skaters_teams.append([1 if player_team == team else 0 for team in teams])

		#Create goalie team indicators so you know which team they are on (for use in FD team constraint)
		for goalie_team in self.goalies_df.loc[:, 'team']:
			self.goalies_teams.append([1 if goalie_team == team else 0 for team in teams])

		#Create goalie opponent indicators so you know who the goalie is opposing
		for player_opp in self.skaters_df.loc[:, 'opp']:
			self.goalies_opponents.append([1 if player_opp == team else 0 for team in self.goalies_df.loc[:, 'team']])

	def generate_lineups(self, formula):
		"""
		Generate n lineups with the forumla's specified constraints.
		"""
		lineups = []
		for _ in tqdm(range(self.num_lineups)):
			lineup = formula(lineups)
			if lineup:
				lineups.append(lineup)
			else:
				break
		return lineups
