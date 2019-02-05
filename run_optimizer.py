import pulp
from termcolor import colored
from nhl.draftkings import Draftkings as NHLDraftkings


#RUN THE NHL OPTIMIZER
################################################################
while True:
	site = input("Select 1 for Draftkings or 2 for Fanduel: ")
	if site not in ('1', '2'):
		print(colored('Try Again...', 'red'))
		continue
	print()
	if site == '1':
		#enter the user parameters
		DK = NHLDraftkings(num_lineups=150,
						overlap=4,
						solver=pulp.CPLEX_PY(msg=0),
						players_filepath = 'nhl/players.csv',
						goalies_filepath = 'nhl/goalies.csv',
						output_filepath = 'nhl/test_output.csv')
		#run the code
		DK.generate_lineups()
	else:
		pass
	break

