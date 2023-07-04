from shtsorter import *


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
