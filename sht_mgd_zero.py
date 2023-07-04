import numpy as np
import os
import ripper as rp


class Shot:
    def __init__(self, number, shtpath, unpack_method):
        self.number = number
        self.shtpath = shtpath
        self.unpack_method = unpack_method
        self.read()

    def read(self):
        if self.unpack_method == "exe":
            filename_sht = f"/sht{self.number}.SHT"
            filename = f"./sht{self.number}.csv"
            if os.name == 'nt':
                os.system(r'test.exe "{0}" "{1}"'.format(self.shtpath + filename_sht, filename))
            else:
                os.system(r'WINEDEBUG=fixme-all LANG=ru_RU.UTF-8 wine test.exe "{0}" "{1}"'.format(self.shtpath + filename_sht, filename))
            try:
                with open(filename, 'r', encoding = "CP1251") as fp:
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
            except:
                pass
        elif self.unpack_method == "shtripper":
                self.names = []
                self.info  = []
                self.unit  = []
                self.data  = []
                var = rp.extract(self.shtpath, self.number)
                for key in var:
                    self.names.append(var[key]["name"])
                    self.info.append(var[key]["comm"])
                    self.unit.append(var[key]["unit"])
                    oscillo = np.asarray(rp.x_y(var[key]))
                    self.data.append(oscillo)
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
            except:
                data.append(np.zeros([9, 4096]))
        return data


class Search:
    def __init__(self,shot,names,cond,cond_val,noise_val,time):
        self.diagnames = names
        self.cond = cond
        self.cond_val = cond_val
        self.shot = shot
        self.res = []
        self.ids = []
        self.noise_val = noise_val
        self.valid_id = 0
        self.time = time
        self.points = [0,0]

    def get_signal_start_time(self):
        try:
            self.find_diagnostics_ids()
            self.find_valid_id()
            if self.valid_id:
                self.set_time_borders()
                t = self.find_signal_start_time()
                return t
            return -1
        except:
            print("Error in time search while reading shot file", self.shot.number, "Empty shot?")
            return -1



    def do_search(self):
        self.find_diagnostics_ids()
        self.find_valid_id()
        if self.valid_id:
            self.set_time_borders()
            #self.apply_filters()
            self.check_condition()
            return
        self.res.append(-1)

    def find_valid_id(self):
        for id in self.ids:
            if id and id != -1:
                diff = abs(max(self.shot.data[id][1]) - min(self.shot.data[id][1]))
                if diff > self.noise_val:
                    self.valid_id = id
                    return

    def find_diagnostics_ids(self):
        i = 0
        for searchname in self.diagnames:
            found_name_flag = 0
            for shotname in self.shot.names:
                if self.shot.unpack_method == "exe":
                    #print(shotname, searchname)
                    decname = shotname[:-1]  # .encode('cp1252').decode('cp1251')
                elif self.shot.unpack_method == "shtripper":
                    decname = shotname
                else:
                    print("incorrect unpack method")
                    decname = "E"
             #print(name, decname, desname)
                if decname == searchname:
                    self.ids.append(i)
                    found_name_flag = 1
                i += 1
            if found_name_flag == 0:
                self.ids.append(-1)
            i = 0
        if self.ids == []:
            print("no such diagnostics, cry about it")

    def set_time_borders(self):
        if self.time != [0,0]:
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
                print("Given time is higher than shot duration")
        else:
            self.time = [0,max(self.shot.data[self.valid_id][0])]
            self.set_time_borders()

    def check_condition(self):
        id = self.valid_id
        maximum = max(abs(self.shot.data[id][1][self.points[0]:self.points[1]]))
        if self.cond == '<':
            #print(maximum)
            if maximum < self.cond_val:
                self.res.append(1)
            else:
                self.res.append(0)
        if self.cond == '>':
            #print(maximum)
            if maximum > self.cond_val:
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


def determine_if_zero(shot,id,zero_border):
    maximum = max(abs(shot.data[id][1]))
    res = 0
    print(maximum)
    if maximum > zero_border:
        res = 1
    else:
        if max(shot.data[id][1]) - min(shot.data[id][1]) > 2*zero_border:
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
                except:
                    pass


def mgd_print_test(shot,columns):
    data = shot.get_data(columns)
    for i in range(len(data)):
        for j in range(len(data[i][0])):
            print(data[i][0][j], data[i][1][j])


def make_output(search,shot,output,unknown):
    unk_flag = 0
    for s in search:
        try:
            s.do_search()
            print(s.res,shot.number)
            if s.res == [1]:
                pass
            elif s.res == [-1]:
                unk_flag = 1
            else:
                return output,unknown
        except:
            print("Error during search while reading shot file", shot.number, "Empty shot?")
            unk_flag = -1
    if unk_flag == 0:
        output.append(shot.number)
    else:
        unknown.append(shot.number)
    return output,unknown


def get_numbers(path):
    numbers = []
    files = [f for f in os.listdir(path)]
    print(files)
    for f in files:
        #print(f)
        #print(f[3:-4])
        numbers.append(int(f[3:-4]))
    print(numbers)
    return numbers


def main():
    output = []
    unknowns_output = []
    #numbers = [43135,43136,43137] #manual shot name input
    numbers = get_numbers("./sht") #read all shot names from directory
    for n in numbers:
        shot = Shot(number=n,
                    shtpath="./sht",
                    unpack_method="exe")
        search_time = Search(shot=shot,
                             names=["Emission electrode current"],
                             cond='>',
                             cond_val=10,
                             noise_val=10,
                             time=[0, 0]) #input [0,0] to search over entire signal
        t_0 = search_time.get_signal_start_time()
        if t_0 != -1:
            search = [Search(shot=shot,
                             names=["МГД  зонд T1 ", "МГД  зонд T2 ", "МГД  зонд T3 ", "МГД  зонд T4 ",
                                    "МГД  зонд T1", "МГД  зонд T2", "МГД  зонд T3", "МГД  зонд T4",
                                    "МГД быстрый зонд T1", "МГД быстрый зонд T2", "МГД быстрый зонд T3",
                                    "МГД быстрый зонд T4"
                                    "МГД быстрый зонд T1 ", "МГД быстрый зонд T2 ", "МГД быстрый зонд T3 ",
                                    "МГД быстрый зонд T4 ",
                                    "МГД быстрый зонд",
                                    "МГД быстрый зонд ",
                                    "МГД быстрый зонд тор.", "МГД быстрый зонд верт.", "МГД быстрый зонд рад.",
                                    "МГД быстрый зонд тор. ", "МГД быстрый зонд верт. ", "МГД быстрый зонд рад. "],
                             cond='<',
                             cond_val=0.4,
                             noise_val=0.4,
                             time=[t_0, t_0 + 0.010]),
                      Search(shot=shot,
                             names=["МГД наружный","МГД наружный  ","МГД наружный   ","МГД наружный    ","МГД наружный     ","МГД наружный      ","МГД наружный       ","МГД наружный        ", ],
                             cond='<',
                             cond_val=0.4,
                             noise_val=0.4,
                             time=[t_0, t_0 + 0.010]),

                      Search(shot=shot,
                             names=["Ip новый (Пр1ВК) (инт.16)", "Ip внутр.(Пр2ВК) (инт.18)", "Ip+Ivv нар.(Пр1ВК) (инт.16)",
                                    "Ip внутр.(Пр2ВК) (инт.18)"],
                             cond='>',
                             cond_val=100_000,
                             noise_val=0.3,
                             time=[t_0, t_0 + 0.010])
                      ]

            output,unknowns_output = make_output(search,shot,output,unknowns_output)
            del (search)
        else:
            print("no emission found", shot.number)
    print("fits all:", output)
    np.savetxt("output.txt", output, fmt="%.5i")
    print("unknown:", unknowns_output)
    np.savetxt("unk_output.txt", unknowns_output, fmt="%.5i")






if __name__ == "__main__":
    main()






