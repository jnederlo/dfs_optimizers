# dfs_optimizers
Optimizers for Daily Fantasy Sports written in python and based on Picking Winners paper.

I describe the concepts of the optimizer in an article I published to Medium:

[DFS Lineup Optimizer with Python](https://medium.com/@jarvisnederlof/dfs-lineup-optimizer-with-python-296e822a5309)

### Run the code examples

It's easy to run the examples as I have it pre-loaded to do so. Just clone the repo, make sure you have all of the dependencies installed (check the requirements.txt file) and then run:

```python3 run_example.py```

This will load in a file from the 'example_inputs' sub-directory of the NHL directory.

### Wait, one more thing
You will need to make sure you have CPLEX installed if you want to run my example as is. You can just use the default solver if you don't want to install CPLEX, but it's much slower. There are also other solvers you can install, but I'll just show you how to install CPLEX. 

Go to [this link](https://www.ibm.com/products/ilog-cplex-optimization-studio) and install the free edition (it will require you to make a free account):

Once you install the one for your system you will still need to set up the python API. 

Instructions to set up the API can be found [here](https://www.ibm.com/support/knowledgecenter/SSSA5P_12.7.1/ilog.odms.cplex.help/CPLEX/GettingStarted/topics/set_up/Python_setup.html)

In short: Find where you installed cplex on your system - on my mac it's in:

`/Applications/CPLEX_Studio_Community128`

then run:

`python setup.py install`

this will install it in you python packages directory, so make sure it goes to the right python packages. For example, I use python3 so I run

`python3 setup.py install`

When I put this on my server and in my python virtual env I had to specify the location of my virtual env python packages like so

`python3 setup.py install --home yourvirtualenvpythonpackageshome/cplex`

Note I also had to go into the above home location (i.e. my virtual env python packages directory and move the cplex folder back a few directories because it was something like 'cplex/ibm/cplex'. So I moved the 2nd cplex to the root of the virtual env packages. Anyways, you probably won't have to do that.

Once you are able to run the setup script then you just follow the instructions and it should be good to go.
