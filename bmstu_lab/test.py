t = int(input())  # Читаем количество наборов данных
for i in range(t):
    s1 = input().strip()  # Читаем вывод участника
    s2 = input().strip()  # Читаем эталонный ответ жюри
    if s1 == s2:
        print("HAPPY_NEW_YEAR!")  # Верный ответ
    else:
        print("WA")  # Неправильный ответ
    input()