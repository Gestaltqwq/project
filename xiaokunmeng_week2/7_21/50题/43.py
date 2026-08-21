import itertools
num_list =['0','1','2','3','4','5','6','7']
result_list = []
count = 0
for i in range(1,9):
    for j in itertools.permutations(num_list,i):
        if j[0] == '0':
            continue
        elif j[-1] not in ['1','3','5','7']:
            continue
        else:
            result = ''.join(j)   
            result_list.append(result)
            count += 1
print(count)