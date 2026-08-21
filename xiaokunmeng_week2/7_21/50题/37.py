def get_out(person_list):
    count = 0
    num_list = []
    for i in range(len(person_list)):
        num_list.append(f"{i}")
    while True:
        for i in range(len(person_list)):
            if person_list[i] != "":
                count += 1
            if count == 3:
                person_list[i] = ""
                count = 0
        count_2 = 0
        while "" in person_list:
            if person_list[count_2] == "":
                person_list.remove(person_list[count_2])
                num_list.remove(num_list[count_2])
            count_2 += 1
        if len(person_list) == 1:
            return int(num_list[0])+1

flag = get_out(["1","2","3","4","5","6","7","8","9"])
print(flag)