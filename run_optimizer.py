import pulp
from termcolor import colored
from nhl.fanduel import Fanduel as NHLFanduel
from nhl.draftkings import Draftkings as NHLDraftkings

#RUN THE NHL OPTIMIZER
################################################################
while True:
	site = input("Select 1 for Draftkings or 2 for Fanduel: ")
	if site not in ('1', '2'):
		print(colored('Try Again...', 'red'))
		continue
	print()
	#set the optimizer based on the user input for the site
	if site == '1':
		#enter the parameters
		optimizer = NHLDraftkings(num_lineups=150,
						   overlap=4,
						   solver=pulp.CPLEX_PY(msg=0),
						   players_filepath = 'nhl/players.csv',
						   goalies_filepath = 'nhl/goalies.csv',
						   output_filepath = 'nhl/test_output_draftkings.csv')
	else:
		#enter the parameters
		optimizer = NHLFanduel(num_lineups=150,
						   overlap=4,
						   solver=pulp.CPLEX_PY(msg=0),
						   players_filepath = 'nhl/players.csv',
						   goalies_filepath = 'nhl/goalies.csv',
						   output_filepath = 'nhl/test_output_fanduel.csv')
		pass
	#create the indicators used to set the constraints to be used by the formula
	optimizer.create_indicators()
	#generate the lineups with the formula and the indicators
	lineups = optimizer.generate_lineups(formula=optimizer.type_1)
	#fill the lineups with player names - send in the positions indicator
	filled_lineups = optimizer.fill_lineups(lineups)
	#save the lineups
	optimizer.save_file(optimizer.header, filled_lineups)
	break

