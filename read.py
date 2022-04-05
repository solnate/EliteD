with open('Kupr.dat') as f:
    nums = f.read().splitlines()

#############################################################
#Так
for kupr in nums:
    nominal = int(kupr.split(',')[0])
    count = int(kupr.split(',')[1])
    print('Номинал - ', nominal, 'кол-во - ',count)

##############################################################
#Или лучше так
separatedNums = dict()
for kupr in nums:
    nominal = int(kupr.split(',')[0])
    count = int(kupr.split(',')[1])
    separatedNums[nominal] = count 

print(separatedNums)
print(separatedNums[5000]) #Если нужно получить количество по номиналу
