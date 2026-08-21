def get_sum(num_list):
    sum = 0
    for i in range(len(num_list)):
        for j in range(len(num_list[i])):
            if i == j or i + j == len(num_list) - 1:
                sum += num_list[i][j]
    return sum

num_list = [
    [7,6,5],
    [5,2,9],
    [1,2,3]
]
print(get_sum(num_list))
