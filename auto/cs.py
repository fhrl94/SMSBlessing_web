import datetime

today = datetime.datetime.today() + datetime.timedelta(days=-7)
print(today.strftime('-%m-%d'))

try:
    datetime.date(today.year,2,29)
except ValueError:
    pass

print(today.now())
print(datetime.datetime.today().date())
datetime.datetime.today().date()
# today = datetime.date(2017,2,28)
# print((today.year%4 == 0 and today.year%100 != 0) or (today.year%400 == 0))

global a
