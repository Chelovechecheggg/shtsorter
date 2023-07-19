from shtsorter import *


def main():
    output = []
    unknowns_output = []
    used_exe = []
    numbers = [42674] # manual shot name input
    # numbers = get_numbers("./sht2")  # read all shot names from directory
    for n in numbers:
        shot = Shot(number=n,
                    shtpath="./sht2",
                    unpack_method="exe")
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
                             cond_val=0.4,
                             filters=["abs"],
                             filt_arg=["none"],
                             noise_val=0.4,
                             time=[t_0, t_0 + 0.010]),
                      Search(shot=shot,
                             names=["Ip новый (Пр1ВК) (инт.16)", "Ip внутр.(Пр2ВК) (инт.18)",
                                    "Ip+Ivv нар.(Пр1ВК) (инт.16)",
                                    "Ip внутр.(Пр2ВК) (инт.18)"],
                             cond='<',
                             cond_val=25000,
                             noise_val=0.0,
                             filters=["diff"],
                             filt_arg=["none"],
                             time=[t_0, t_0 + 0.010]),
                      Search(shot=shot,
                             names=["МГД наружный", "МГД наружный  ", "МГД наружный   ", "МГД наружный    ",
                                    "МГД наружный     ", "МГД наружный      ", "МГД наружный       ",
                                    "МГД наружный        ", ],
                             cond='<',
                             cond_val=0.4,
                             filters=["abs"],
                             filt_arg=["none"],
                             noise_val=0.4,
                             time=[t_0, t_0 + 0.010]),

                      Search(shot=shot,
                             names=["Ip новый (Пр1ВК) (инт.16)", "Ip внутр.(Пр2ВК) (инт.18)",
                                    "Ip+Ivv нар.(Пр1ВК) (инт.16)",
                                    "Ip внутр.(Пр2ВК) (инт.18)"],
                             cond='>',
                             cond_val=100_000,
                             noise_val=0.3,
                             filters=[],
                             filt_arg=[],
                             time=[t_0, t_0 + 0.010]),
                      Search(shot=shot,
                             names=["Emission electrode current"],
                             cond='>',
                             cond_val=3,
                             noise_val=3,
                             filters=[],
                             filt_arg = [],
                             time=[t_0, t_0 + 0.010]),
                      Search(shot=shot,
                             names=["Emission electrode current"],
                             cond='<',
                             cond_val=0.00148,
                             noise_val=0,
                             filters=["+", "avg", "/diagn_avg"],
                             filt_arg=[9.995, "none", "Emission electrode voltage"],
                             time=[t_0, t_0 + 0.010])
                      ]

            output, unknowns_output, used_exe = make_output(search, shot, output, unknowns_output, used_exe)
        else:
            print("no emission found", shot.number)
    print("fits all:", output)
    np.savetxt("output.txt", output, fmt="%.5i")
    print("unknown:", unknowns_output)
    np.savetxt("unk_output.txt", unknowns_output, fmt="%.5i")
    print("used exe unpack method:", used_exe)
    np.savetxt("exe_output.txt", used_exe, fmt="%.5i")


if __name__ == "__main__":
    main()
