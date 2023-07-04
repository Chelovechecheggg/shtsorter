# shtsorter
## Description
A script made for finding Globus-M2 tokamak shots that meet specific condition.
Named "shtsorter" because "shtfinder" already exists but does something else
## Usage
Open run.py to configure the search conditions. <p>
***Shot*** class is created to read all data from a shot. Available parameters: <br>
- **shtpath** - path to the folder that contains all the .sht files. If changed, also change it in the get_numbers function <br>
- **unpack_method** - either "exe" or "shtripper". "exe" is used for faster file reading (~2-3s to read one .sht file),
however not every data point is used<br>, which may lead to missing short spikes in the signal. "shtripper" reads all data points,
however it takes ~2 minutes to read one .sht file. <p>

***search_time*** is used to set time interval relative to a signal from a diagnostic. Available parameters: <br>
- **names** - names of the diagnostics to look for. Uses the first diagnostic that is found
in a shot file. <br>
- **cond** and **cond_val** - *cond* is either "<" or ">" (for now). The program will look at which
time point the signal becomes less or greater (depending on *cond*) than *cond_val* and will set
variable t_0 to that time.<br>
- **noise_val** - the value that determines empty signals. If the difference between maximum and minimum
values of a signal in a diagnostic is less than **noise_val** for the entire duration of a shot, the program will
not use the diagnostic.<br>
- **time** - time interval in which the program looks for a signal. in *search_time* should be set to [0,0]

***search*** is used to actually set the search conditions. Available parameters: <br>
- **names** - sames as in *search_time*
- **cond** and **cond_val** - *cond* is either "<" or ">" (for now). The program will look for
shots with signal value less or greater (depending on *cond*) that *cond_val* in the given
time interval
- **noise_val** - same as in *search_time*
- **time** - same as in *search_time*. Here the variable t_0 can be used to set the time interval
relative to a signal from a diagnostic signal specified in *search_time* <br>
- Here multiple "Search" objects can be created and put in an array. In that case the program will look for
shots that meets search conditions from all objects in an array.