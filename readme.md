# shtsorter
## Description
A script made for finding Globus-M2 tokamak shots that meet specific conditions.
Named "shtsorter" because "shtfinder" already exists but does something else
## Usage
Open run.py to configure the search conditions.
Description of all the available settings and search conditions is provided below <p>
**search_name** is the name that will be given to all output files. <p>
**makeheaders** function is used for making headers for output files. First argument should be the name of the run file
("run.py" by default), and the second argument is the name of the output file (should be the search_name variable)<p>
***Shot*** class is created to read all data from a shot. Available parameters: <br>
- **shtpath** - path to the folder that contains all the .sht files. If changed, also change it in the get_numbers function <br>
- **unpack_method** - either "exe" or "shtripper". "exe" is used for faster file reading (~2-3s to read one .sht file),
however not every data point is used<br>, which may lead to missing short spikes in the signal. "shtripper" reads all data points,
however it takes ~2 minutes to read one .sht file.
- **searchname** - string that will be used to name all output files. Should be the *search_name* variable. Must match *search_name* in the
*make_headers* function.<p>
**THE PROGRAM CLEARS OUTPUT FILES WITH THE SAME SEARCH_NAME WHEN LAUNCHING. MAKE SURE TO SAVE ALL INFO THAT YOU NEED FROM
THOSE FILES OR TO CHANGE THE SEARCH_NAME BEFORE LAUNCHING THE PROGRAM AGAIN**<p>

***search_time*** is used to set time interval relative to a signal from a diagnostic. Available parameters: <br>
- **names** - names of the diagnostics to look for. Uses the first diagnostic that is found
in a shot file. <br>
- **cond** and **cond_val** - *cond* is either "<" or ">". The program will look at which
time point the signal becomes less or greater (depending on *cond*) than *cond_val* and will set
variable t_0 to that time.<br>
- **noise_val** - the value that determines empty signals. If the difference between maximum and minimum
values of a signal in a diagnostic is less than **noise_val** for the entire duration of a shot, the program will
not use the diagnostic.<br>
- **time** - time interval in which the program looks for a signal. in *search_time* should be set to [0,0] <br>
- **filters** and **filt_arg** - are not used in *search_time*

***search*** is used to actually set the search conditions. Available parameters: <br>
- **names** - same as in *search_time*
- **cond** and **cond_val** - *cond* can be "<", ">", "<once", ">once". The program will look for
shots where all values of a signal is less or greater (if *cond* is "<" or ">" respectively) that *cond_val* in the given
time interval. If *cond* is "<once" or ">once" the program will look for shots where at least one point in the signal
is less than/greater than *cond_val* (respectively)
- **noise_val** - same as in *search_time*
- **time** - same as in *search_time*. Here the variable t_0 can be used to set the time interval
relative to a signal from a diagnostic signal specified in *search_time* <br>
- Here multiple "Search" objects can be created and put in an array. In that case the program will look for
shots that meets search conditions from all objects in an array. <br>
- **filters** and **filt_arg** - read below

The program creates four txt files when launched: *log.txt*, *output.txt*, *output_unk.txt*, *output_exe.txt*.
Each file begins with a header containing the date and time of the program launch and all search settings used
during that launch. *log.txt* file contains (mostly) everything that is displayed in the terminal: successes/failures 
of each search condition, errors and warnings. Used mostly for debugging and is not cleared after each launch. 
The *log.txt* file should be manually deleted/cleared from time to time. *output* contains the numbers of all the shot
files that fit the conditions. *output_unk* is used for the cases when an error occurred when checking some
of the search criteria, but there were no checks that the shot didn't pass. The shots end up in this
folder very rarely, and they should be analyzed manually. *output_exe* is only used with *shtripper* unpack method.
If an error occurs when unpacking with *shtripper* method (which sometimes happens for some reason),
the *exe* method will be used instead. If then a shot passes all checks, it will be saved to *output_exe* file instead
of *output*<p>

## Filters 
Filters are used to search not only for signal values themselves, 
but also for other information contained in a signal, like average values or rate of growth.
If there are filters in the *filters* list the program applies the selected filters to the signal in order from first
to last before comparing it to the specified condition. <br>
The amount of variables in *filters* and *filt_arg* lists must be the same. The first argument is used for the first
filter, the second argument is used for the second filter and so on. If a filter requires no
arguments, put "none" as the argument for it. <br>
Available filters:
- **"+"**, **"-"**, **"*"**, **"/"**, **"^"** - adds/subtracts/multiplies/divides the signal by/raises the signal to a
power of (respectively) a value
    - Argument: any real number
- **der** - calculates a numerical derivative of a signal at each point. 
    - No arguments required: insert "none" as the argument
- **avg** - calculates the average value of a signal on a given time interval.
    -   No arguments required: insert "none" as the argument
- **abs** - calculates the absolute value of each data point in a signal
    - No arguments required: insert "none" as the argument
- **"+diagn"**, **"-diagn"**, **"*diagn"**, **"/diagn"**, **"^diagn"** - adds to the signal/subtracts from a signal/multiplies/divides the signal by/raises the signal to a
power of (respectively) a signal from a different diagnostic
    - Argument: list with names of the diagnostics. The operation will be performed with the first 
  valid(existing with non-noise signal) diagnostic in the list
- **"+diagn_avg"**, **"-diagn_avg"**, **"*diagn_avg"**, **"/diagn_avg"**, **"^diagn_avg"** - adds to the signal/subtracts from a signal/multiplies/divides the signal by/raises the signal to a
power of (respectively) the average value of signal from a different diagnostic on the given time interval.
    - Argument: list with names of the diagnostics. The operation will be performed with the first 
  valid(existing with non-noise signal) diagnostic in the list
- **"stft_freq"** - computes short time Fourier transform of the signal and returns magnitude change over time of
the signal on the given frequency
    - Argument: integer, the frequency mentioned above.
    - **Should only be used with "shtripper" unpack method.** "exe" unpack method returns inconsistent data or errors
  due to low number of data points 
- **"smooth"** - smoothes the signal using Savitzky-Golay algorithm
    - No arguments required: insert "none" as the argument 
  
