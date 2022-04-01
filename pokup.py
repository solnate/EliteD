
nominal = [5000, 2000, 1000]
def pokup(balance):
    while True:
        try:
            countOfBill = int(input('Кол-во номиналов: '))
        except ValueError:
                print("Вы ввели не число. Попробуйте снова")
        else:
            break

    billNominals = []
    while countOfBill:
        try:
            tempIn = int(input('Введите номинал: '))
        except ValueError:
            print('Вы ввели не число. Попробуйте снова')
        else:
            if tempIn in nominal:
                billNominals.append(tempIn)
                countOfBill -= 1
            else:
                print('Неправильный номинал')
        
    for billNominal in billNominals:
        countOfBill = int(balance/billNominal)
        balance = balance%billNominal
        print('Номинал купюр:', billNominal, ' - Количество:', countOfBill)
    
    print('Осталось', balance)

pokup(16000)