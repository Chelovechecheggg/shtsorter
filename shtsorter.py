import numpy as np
import os
import ripper as rp
import statistics as st
import scipy as sp


class Shot:
    def __init__(self, number, shtpath, unpack_method):
        self.number = number
        self.shtpath = shtpath
        self.unpack_method = unpack_method
        self.names = []
        self.info = []
        self.unit = []
        self.data = []
        self.read()

    def read(self):
        if self.unpack_method == "exe":
            filename_sht = f"/sht{self.number}.SHT"
            filename = f"./sht{self.number}.csv"
            if os.name == 'nt':
                os.system(r'test.exe "{0}" "{1}"'.format(self.shtpath + filename_sht, filename))
            else:
                os.system(r'WINEDEBUG=fixme-all LANG=ru_RU.UTF-8 wine test.exe "{0}" "{1}"'.format(
                    self.shtpath + filename_sht, filename))
            try:
                with open(filename, 'r', encoding="CP1251") as fp:
                    line = fp.readline()
                    n_oscillo = int(line)
                    self.names = []
                    self.info = []
                    self.unit = []
                    self.data = []
                    for _ in range(n_oscillo):
                        line = fp.readline()
                        self.names.append(line)
                        line = fp.readline()
                        self.info.append(line)
                        line = fp.readline()
                        self.unit.append(line)
                        line = fp.readline()
                        length = int(line)
                        oscillo = np.zeros([2, length])
                        for idx in range(length):
                            line = fp.readline().split()
                            for i in range(oscillo.shape[0]):
                                oscillo[i, idx] = float(line[i])
                        self.data.append(oscillo)
                os.remove(filename)
            except Exception as e:
                print(e)

        elif self.unpack_method == "shtripper":
            try:
                self.names = []
                self.info = []
                self.unit = []
                self.data = []
                var = rp.extract(self.shtpath, self.number)
                for key in var:
                    self.names.append(var[key]["name"])
                    self.info.append(var[key]["comm"])
                    self.unit.append(var[key]["unit"])
                    oscillo = np.asarray(rp.x_y(var[key]))
                    self.data.append(oscillo)
            except Exception as e:
                print(e)
                print("In shot", self.number, "shtripper unpack method didnt work. Using exe method instead...")
                self.unpack_method = "exe"
                self.read()
        else:
            raise NameError('No such unpack_method')

    def print_names(self):
        i = 0
        for name in self.names:
            print(i, name)
            i += 1

    def get_ip(self):
        ip_idx = 1
        return np.sort(self.data[ip_idx][1])[-100:-1].mean()

    ''' requires matplotlib to work, is not currently used
    def plot(self, idx, fig_num=None, color='k'):
        plt.figure(fig_num)
        plt.grid(True)
        plt.xlabel("t, ms")
        plt.ylabel(self.unit[idx])
        plt.title(self.names[idx])
        plt.plot(self.data[idx][0], self.data[idx][1], color=color)'''

    def get_data(self, columns):
        data = []
        for col in columns:
            try:
                data.append(self.data[col])
            except Exception as e:
                print(e)
                data.append(np.zeros([9, 4096]))
        return data


class Search:
    def __init__(self, shot, names, cond, cond_val, filters, filt_arg, noise_val, time):
        self.diagnames = names
        self.cond = cond
        self.cond_val = cond_val
        self.shot = shot
        self.res = []
        self.ids = []
        self.processed_data = np.array([])
        self.processed_time = np.array([])
        self.filters = filters
        self.filt_arg = filt_arg
        self.noise_val = noise_val
        self.valid_id = 0
        self.time = time
        self.points = [0, 0]

    def get_signal_start_time(self):
        try:
            self.find_diagnostics_ids()
            self.find_valid_id()
            if self.valid_id:
                self.set_time_borders()
                t = self.find_signal_start_time()
                return t
            return -1
        except Exception as e:
            print(e)
            print("Error in time search while reading shot file", self.shot.number, "Empty shot?")
            return -1

    def do_search(self):
        self.find_diagnostics_ids()
        self.find_valid_id()
        if self.valid_id:
            self.set_time_borders()
            self.apply_filters()
            self.check_condition()
            return
        self.res.append(-1)

    def find_valid_id(self):
        self.valid_id = 0
        for shot_id in self.ids:
            if shot_id and shot_id != -1:
                diff = abs(max(self.shot.data[shot_id][1]) - min(self.shot.data[shot_id][1]))
                if diff > self.noise_val:
                    self.valid_id = shot_id
                    return

    def find_diagnostics_ids(self):
        i = 0
        self.ids = []
        for searchname in self.diagnames:
            found_name_flag = 0
            for shotname in self.shot.names:
                if self.shot.unpack_method == "exe":
                    # print(shotname, searchname)
                    decname = shotname[:-1]  # .encode('cp1252').decode('cp1251')
                elif self.shot.unpack_method == "shtripper":
                    decname = shotname
                else:
                    print("incorrect unpack method in shot", self.shot.number)
                    decname = "E"
                # print(name, decname, desname)
                if decname == searchname:
                    self.ids.append(i)
                    found_name_flag = 1
                i += 1
            if found_name_flag == 0:
                self.ids.append(-1)
            i = 0
        if not self.ids:
            print("no such diagnostics, cry about it. In shot", self.shot.number)

    def set_time_borders(self):
        if self.time != [0, 0]:
            min_diff = 9999
            i = 0
            for step in self.shot.data[self.valid_id][0]:
                if min_diff > abs(step - self.time[0]):
                    min_diff = abs(step - self.time[0])
                    self.points[0] = i
                i = i + 1
            min_diff = 9999
            i = 0
            for step in self.shot.data[self.valid_id][0]:
                if min_diff > abs(step - self.time[1]):
                    min_diff = abs(step - self.time[1])
                    self.points[1] = i
                i = i + 1
            if self.time[1] > max(self.shot.data[self.valid_id][0]):
                print("Given time is higher than shot duration in shot", self.shot.number)
        else:
            self.time = [0, max(self.shot.data[self.valid_id][0])]
            self.set_time_borders()

    def apply_filters(self):
        self.processed_data = self.shot.data[self.valid_id][1][self.points[0]:self.points[1]]
        self.processed_time = self.shot.data[self.valid_id][0][self.points[0]:self.points[1]]
        operator_dict = {"+": np.add, "-": np.subtract, "*": np.multiply, "/": np.divide, "^": np.power}
        operator_dict_diagn = {"+diagn": np.add, "-diagn": np.subtract, "*diagn": np.multiply, "/diagn": np.divide,
                               "^diagn": np.power}
        operator_dict_diagn_max = {"+diagn_avg": np.add, "-diagn_avg": np.subtract, "*diagn_avg": np.multiply,
                                   "/diagn_avg": np.divide, "^diagn_avg": np.power}
        for f, f_arg in zip(self.filters, self.filt_arg):
            if f == "abs":
                self.processed_data = abs(self.processed_data)
            if f == "avg":
                avg = st.mean(self.processed_data)
                self.processed_data = np.array([avg])
                self.processed_time = np.array([0])
                print(self.processed_data)
            elif f in operator_dict.keys():
                oper = operator_dict[f]
                self.processed_data = oper(self.processed_data, f_arg)
            elif f == "der":
                self.processed_data = np.gradient(self.processed_data)
            elif f in operator_dict_diagn.keys():
                oper = operator_dict_diagn[f]
                self.diagnames = [f_arg]
                self.find_diagnostics_ids()
                self.find_valid_id()
                self.processed_data = oper(self.processed_data,
                                           self.shot.data[self.valid_id][1][self.points[0]:self.points[1]])
            elif f in operator_dict_diagn_max.keys():
                oper = operator_dict_diagn_max[f]
                self.diagnames = [f_arg]
                self.find_diagnostics_ids()
                self.find_valid_id()
                if self.valid_id:
                    maxm = st.mean(self.shot.data[self.valid_id][1][self.points[0]:self.points[1]])
                    self.processed_data = oper(self.processed_data,
                                               maxm)
            elif f == "diff":
                self.processed_data = self.processed_data[self.points[1]]-self.processed_data[self.points[0]]
            elif f == "sawtooth":
                pass  # WIP
            elif f == "stft_freq":
                freq = f_arg[0]
                stft_freq, t, zxx = sp.signal.stft(x=self.processed_data, nperseg=f_arg[1], noverlap=f_arg[2],
                                                   nfft=f_arg[3], fs=f_arg[4])
                # print(zxx)
                if freq > max(stft_freq):
                    print("Warning during STFT in shot", self.shot.number, ": given frequency is larger than max"
                                                                           "stft frequency")
                stft_freq = abs(stft_freq-freq)
                s_fr_min = 9999999
                n_min = -1
                for n, s_fr in zip(range(len(stft_freq)), stft_freq):
                    if s_fr < s_fr_min:
                        n_min = n
                        s_fr_min = s_fr
                self.processed_data = abs(zxx[n_min])
                self.points[0] = 0
                self.points[1] = len(self.processed_data)-1
                if n_min == -1:
                    print("Error during STFT in shot", self.shot.number, "*very* invalid frequency given ")

    def check_condition(self):
        maximum = max(self.processed_data)
        minimum = min(self.processed_data)
        if self.cond == '<':
            # print(maximum)
            if maximum < self.cond_val:
                self.res.append(1)
            else:
                self.res.append(0)
        if self.cond == '>':
            # print(maximum)
            if minimum > self.cond_val:
                self.res.append(1)
            else:
                self.res.append(0)

    def find_signal_start_time(self):
        i = 0
        for signal in self.shot.data[self.valid_id][1]:
            if signal > self.cond_val:
                return self.shot.data[self.valid_id][0][i]
            i = i + 1
        return -1


def determine_if_zero(shot, shot_id, zero_border):
    maximum = max(abs(shot.data[shot_id][1]))
    res = 0
    print(maximum)
    if maximum > zero_border:
        res = 1
    else:
        if max(shot.data[shot_id][1]) - min(shot.data[shot_id][1]) > 2 * zero_border:
            res = 2
    print(res)


def find_encoding(shot):
    codes = ['koi8-r', 'unicode', 'cp850', 'cp866', 'utf-8', 'cp1251', 'cp1252']
    for name in shot.names:
        for i in codes:
            for j in codes:
                print("current pair:", i, j)
                try:
                    print(name[:-1].encode(i).decode(j))
                except Exception as e:
                    print(e)
                    pass


def mgd_print_test(shot, columns):
    data = shot.get_data(columns)
    for i in range(len(data)):
        for j in range(len(data[i][0])):
            print(data[i][0][j], data[i][1][j])


def make_output(search, shot, output, unknown):
    unk_flag = 0
    for s in search:
        try:
            s.do_search()
            print(s.res, shot.number)
            if s.res == [1]:
                pass
            elif s.res == [-1]:
                unk_flag = 1
            else:
                return output, unknown
        except Exception as e:
            print(e)
            print("Error during search while reading shot file", shot.number, "Empty shot?")
            unk_flag = -1
    if unk_flag == 0:
        output.append(shot.number)
    else:
        unknown.append(shot.number)
    return output, unknown


def get_numbers(path):
    numbers = []
    files = [f for f in os.listdir(path)]
    print(files)
    for f in files:
        # print(f)
        # print(f[3:-4])
        numbers.append(int(f[3:-4]))
    print(numbers)
    return numbers
