from shtsorter import *


def main():
    search_name = ""
    make_headers(runname="run.py",
                 search_name=search_name)
    output = []
    unknowns_output = []
    used_exe = []
    # numbers = [42068]  # manual shot name input
    numbers = get_numbers(path="./sht2",
                          min_number=0,
                          max_number=99999)
    for n in numbers:
        shot = Shot(number=n,
                    shtpath="./sht2",
                    unpack_method="exe",
                    searchname=search_name)
        search_time = Search(shot=shot,
                             names=["Emission electrode current"],
                             cond='>',
                             cond_val=10,
                             filters=[],
                             filt_arg=[],
                             noise_val=10,
                             time=[0, 0])  # input [0,0] to search over entire signal
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
                             cond_val=0.3,
                             filters=["abs"],
                             filt_arg=["none"],
                             noise_val=0.3,
                             time=[t_0, t_0 + 0.020]),
                      Search(shot=shot,
                             names=["Ip новый (Пр1ВК) (инт.16)", "Ip внутр.(Пр2ВК) (инт.18)",
                                    "Ip+Ivv нар.(Пр1ВК) (инт.16)",
                                    "Ip внутр.(Пр2ВК) (инт.18)"],
                             cond='<',
                             cond_val=25000,
                             noise_val=0.0,
                             filters=["diff"],
                             filt_arg=["none"],
                             time=[t_0, t_0 + 0.020]),
                      Search(shot=shot,
                             names=["Лазер", "Лазер ", "Лазер  "],
                             cond='<once',
                             cond_val=-0.3,
                             noise_val=0.0,
                             filters=[],
                             filt_arg=[],
                             time=[t_0, t_0 + 0.020]),
                      Search(shot=shot,
                             names=["МГД наружный", "МГД наружный  ", "МГД наружный   ", "МГД наружный    ",
                                    "МГД наружный     ", "МГД наружный      ", "МГД наружный       ",
                                    "МГД наружный        ", ],
                             cond='<',
                             cond_val=0.3,
                             filters=["abs"],
                             filt_arg=["none"],
                             noise_val=0.3,
                             time=[t_0, t_0 + 0.020]),

                      Search(shot=shot,
                             names=["Ip новый (Пр1ВК) (инт.16)", "Ip внутр.(Пр2ВК) (инт.18)",
                                    "Ip+Ivv нар.(Пр1ВК) (инт.16)",
                                    "Ip внутр.(Пр2ВК) (инт.18)"],
                             cond='>',
                             cond_val=100_000,
                             noise_val=0.3,
                             filters=[],
                             filt_arg=[],
                             time=[t_0, t_0 + 0.020]),
                      Search(shot=shot,
                             names=["Emission electrode current"],
                             cond='>',
                             cond_val=3,
                             noise_val=3,
                             filters=[],
                             filt_arg=[],
                             time=[t_0, t_0 + 0.020]),
                      Search(shot=shot,
                             names=["Emission electrode current"],
                             cond='<',
                             cond_val=0.00148,
                             noise_val=0,
                             filters=["+", "avg", "/diagn_avg"],
                             filt_arg=[9.995, "none", "Emission electrode voltage"],
                             time=[t_0, t_0 + 0.020])
                      ]

            output, unknowns_output, used_exe = make_output(search, shot, output, unknowns_output, used_exe)
        else:
            print("no emission found", shot.number)
            f_log = open(f"out/{shot.search_name}log.txt", "a")
            f_log.write("no emission found" + " " + repr(shot.number) + "\n")
            f_log.close()
    print("fits all:", output)
    print("unknown:", unknowns_output)
    print("used exe unpack method:", used_exe)


if __name__ == "__main__":
    main()
