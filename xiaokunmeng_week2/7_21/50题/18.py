alpha = ['a','b','c']
beta = ['x','y','z']
alpha_done = []
beta_done = []
competition_list = []
while True:
    for i in alpha:
        for j in beta:
            if i == 'a' and j == 'x':
                continue
            elif i == 'c' and j == 'x' or i == 'c' and j == 'z':
                continue
            else:
                if i not in alpha_done and j not in beta_done:
                    competition_list.append((i,j))
                    alpha_done.append(i)
                    beta_done.append(j)
    for m in alpha:
        if m not in alpha_done:
            alpha_done = []
            beta_done = []
            competition_list = []
            alpha.append(alpha.pop(0))
            break
    if competition_list == []:
        continue
    break

print(competition_list)



