import matplotlib.pyplot as plt
import numpy as np
import os
import ripper as rp
import statistics as st
import scipy as sp
from datetime import datetime
import shtRipper as rp_but_cooler

global B, stft, time, zxx2

class Shot:
    def __init__(self, number, shtpath, unpack_method, searchname):
        self.number = number
        self.shtpath = shtpath
        self.unpack_method = unpack_method
        self.names = []
        self.info = []
        self.unit = []
        self.data = []
        self.ripper_fail_flag = 0
        self.search_name = str(searchname)
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
                #var = rp.extract(self.shtpath, self.number)
                var = rp_but_cooler.ripper.read(self.shtpath + "/sht" + str(self.number) + ".SHT")
                #print(var.keys())
                if var == {}:
                    raise ValueError('Empty shot ', self.number)
                for key in var.keys():
                    self.names.append(key)
                    self.info.append(var[key]["comment"])
                    self.unit.append(var[key]["unit"])
                    #oscillo = np.asarray(rp.x_y(var[key]))
                    #self.data.append(oscillo)
                    self.data.append([var[key]['x'],var[key]['y']])
            except Exception as e:
                print(e)
                print("In shot", self.number, "shtripper unpack method didnt work. Using exe method instead...")
                f_log = open(f"out/{self.search_name}log.txt", "a")
                f_log.write(str(e) + "\n")
                f_log.write("In shot " + str(self.number) + " shtripper unpack method didnt work. Using exe "
                            "method instead..." + "\n")
                f_log.close()
                self.unpack_method = "exe"
                self.ripper_fail_flag = 1
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

    def plot(self, idx, fig_num=None, color='k'):
        plt.figure(fig_num)
        plt.grid(True)
        plt.xlabel("t, ms")
        plt.ylabel(self.unit[idx])
        plt.title(self.names[idx])
        plt.plot(self.data[idx][0], self.data[idx][1], color=color)

    def get_data(self, columns):
        data = []
        for col in columns:
            try:
                data.append(self.data[col])
            except Exception as e:
                print(e)
                f_log = open(f"out/{self.search_name}log.txt", "a")
                f_log.write(str(e) + "\n")
                f_log.close()
                data.append(np.zeros([9, 4096]))
        return data


class Search:
    def __init__(self, shot, names, cond, cond_val, filters, filt_arg, noise_val, time, or_group):
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
        self.f_log = open(f"out/{shot.search_name}log.txt", "a")
        self.or_group = or_group

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
            self.f_log.write(repr(e) + "\n")
            self.f_log.write("Error in time search while reading shot file" + repr(self.shot.number) + "Empty shot?"
                             + "\n")
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
                    self.f_log.write("incorrect unpack method in shot" + repr(self.shot.number) + "\n")
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
            self.f_log.write("no such diagnostics, cry about it. In shot" + repr(self.shot.number) + "\n")

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
                self.f_log.write("Given time is higher than shot duration in shot" + repr(self.shot.number) + "\n")
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

            elif f in operator_dict.keys():
                #global B
                oper = operator_dict[f]
                self.processed_data = oper(self.processed_data, f_arg)
                print(self.processed_data)
                #B = self.processed_data
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
                self.processed_data = np.array([self.processed_data[-1]-self.processed_data[0]])
                self.processed_time = np.array([0])
            elif f == "sawtooth":
                pass  # WIP
            elif f == "stft_freq":

                freq = f_arg[0]
                stft_freq, t, zxx = sp.signal.stft(x=self.processed_data, nperseg=f_arg[1], noverlap=f_arg[2],
                                                   nfft=f_arg[3], fs=f_arg[4], scaling= f_arg[5])
                global stft, time, zxx2, img_flag
                img_flag = 0
                if f_arg[6] == 1:
                    stft, time, zxx2, img_flag = stft_freq, t, zxx, 1
                '''plt.figure(figsize=(19, 11))
                cmap = plt.colormaps["jet"]
                plt.pcolormesh(t, stft_freq, abs(zxx), vmin=0,
                               vmax=np.max(abs(zxx)) * 0.98, cmap=cmap)
                plt.title(f'STFT MHD. Power spectral density\n' + f'Shot #, Selected burst  ms',
                          fontsize=20)
                plt.ylabel('Frequency, kHz', fontsize=18)
                plt.xlabel('Time, ms', fontsize=18)
                # plt.ylim(f_window[0], f_window[1])
                # plt.xlim(time_window[0], time_window[1])
                plt.colorbar()
                # plt.show()

                plt.savefig(f'out/images/{self.shot.number}.png')'''
                # print(zxx)
                if freq > max(stft_freq):
                    print("Warning during STFT in shot", self.shot.number, ": given frequency is larger than max"
                                                                           "stft frequency")
                    self.f_log.write("Warning during STFT in shot " + str(self.shot.number) +
                                     ": given frequency is larger than max stft frequency" + "\n")
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
                    self.f_log.write("Error during STFT in shot " + str(self.shot.number) +
                                     " *very* invalid frequency given" + "\n")
            elif f == "smooth":
                self.processed_data = sp.signal.savgol_filter(x=self.processed_data,
                                                              window_length=int(len(self.processed_data)/2),
                                                              polyorder=4)

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
        if self.cond == '>once':
            for val in self.processed_data:
                if val > self.cond_val:
                    self.res.append(1)
                    return
            self.res.append(0)
        if self.cond == '<once':
            for val in self.processed_data:
                if val < self.cond_val:
                    self.res.append(1)
                    return
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


def save_stft_image(shot, stft_freq, t, zxx): #,B
    plt.figure(figsize=(19, 11))
    cmap = plt.colormaps["jet"]
    plt.pcolormesh(t, stft_freq, abs(zxx), vmin=0,
                   vmax=np.max(abs(zxx)) * 0.98, cmap=cmap)
    plt.title(f'STFT MHD. Power spectral density\n' + f'Shot #{shot.number}',
              fontsize=20)
    plt.ylabel('Frequency, kHz', fontsize=18)
    plt.xlabel('Time, ms', fontsize=18)
    plt.xticks(ticks=[0,12/1200,2*12/1200,3*12/1200,4*12/1200,5*12/1200,6*12/1200,7*12/1200,8*12/1200,9*12/1200,10*12/1200,11*12/1200,12*12/1200],labels=[130,140,150,160,170,180,190,200,210,220,230,240,250])
    # plt.ylim(f_window[0], f_window[1])
    # plt.xlim(time_window[0], time_window[1])
    plt.colorbar()
    # plt.show()

    plt.savefig(f'out/images/{str(shot.number)}')   # + ' ' + str(B[0])}.png'
    plt.close()


def make_output(search, shot, output, unknown, used_exe):
    unk_flag = 0
    last_or_group = -1
    last_res = -2
    f_output = open(f"out/{shot.search_name}output.txt", "a")
    f_unk = open(f"out/{shot.search_name}output_unk.txt", "a")
    f_exe = open(f"out/{shot.search_name}output_exe.txt", "a")
    for s in search:
        try:
            if s.or_group == last_or_group:
                if last_res == 1:
                    continue
                else:
                    pass
            else:
                if last_res == 0:
                    return output, unknown, used_exe
            last_or_group = s.or_group
            s.do_search()
            print(s.res, shot.number)
            s.f_log.write(repr(s.res) + " " + repr(shot.number) + "\n")
            if s.res == [1]:
                last_res = 1
                pass
            elif s.res == [-1]:
                unk_flag = 1
                last_res = -1
            else:
                last_res = 0
                #return output, unknown, used_exe
        except Exception as e:
            print(e)
            print("Error during search while reading shot file", shot.number, "Empty shot?")
            s.f_log.write(repr(e) + "\n")
            s.f_log.write("Error during search while reading shot file" + repr(shot.number) + "Empty shot?" + "\n")
            unk_flag = -1
    if unk_flag == 0 and shot.ripper_fail_flag == 0 and last_res != 0:
        global stft, time, zxx2, img_flag #, B
        output.append(str(shot.number)) # + ", B = " + str(B)
        f_output.write(repr(shot.number) + "\n")
        if img_flag == 1:
            save_stft_image(shot,stft,time,zxx2)

    elif unk_flag == 1 and shot.ripper_fail_flag == 0:
        unknown.append(shot.number)
        f_unk.write(repr(shot.number) + "\n")
    elif shot.ripper_fail_flag == 1:
        used_exe.append(shot.number)
        f_exe.write(repr(shot.number) + "\n")
    return output, unknown, used_exe




def get_numbers(path, min_number, max_number):
    numbers = []
    files = [f for f in os.listdir(path)]
    print(files)
    for f in files:
        # print(f)
        # print(f[3:-4])
        if min_number < int(f[3:-4]) < max_number:
            numbers.append(int(f[3:-4]))
    print(numbers)
    return numbers

def get_numbers_img(path, min_number, max_number):
    numbers = []
    files = [f for f in os.listdir(path)]
    print(files)
    for f in files:
        # print(f)
        #print(f[0:5])
        if min_number < int(f[0:5]) < max_number:
            numbers.append(int(f[0:5]))
    print(numbers)
    return numbers


def make_headers(runname, search_name):
    try:
        os.remove(f"out/{search_name}output.txt")
        os.remove(f"out/{search_name}output_unk.txt")
        os.remove(f"out/{search_name}output_exe.txt")
    except Exception as e:
        print(e)
        pass

    f_log = open(f"out/{search_name}log.txt", "a")
    f_out = open(f"out/{search_name}output.txt", "a")
    f_unk = open(f"out/{search_name}output_unk.txt", "a")
    f_exe = open(f"out/{search_name}output_exe.txt", "a")
    f_run = open(runname, "r")
    header = f_run.read()
    header_start = 0
    for a in range(len(header)):
        if header[a] == "S" and header[a+1] == "h" and header[a+2] == "o" and header[a+3] == "t":
            header_start = a
            break
    f_log.write("========================= Launch as of " + str(datetime.now()) + " =========================" + "\n")
    f_log.write(header[header_start:-484] + "\n" + " ====================================" + "\n")
    f_out.write("========================= Launch as of " + str(datetime.now()) + " =========================" + "\n")
    f_out.write(header[header_start:-484] + "\n" + " ====================================" + "\n")
    f_unk.write("========================= Launch as of " + str(datetime.now()) + " =========================" + "\n")
    f_unk.write(header[header_start:-484] + "\n" + " ====================================" + "\n")
    f_exe.write("========================= Launch as of " + str(datetime.now()) + " =========================" + "\n")
    f_exe.write(header[header_start:-484] + "\n" + " ====================================" + "\n")
    f_log.close()
    f_out.close()
    f_unk.close()
    f_exe.close()

