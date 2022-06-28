import re

diffFile = open('example.txt', "r")
diff = diffFile.read()
matches = re.findall(r"[-](.*)[\n][+](.*)", diff)
for match in matches:
    for d in match:
        print(d.strip())
    print('--------------------------------END-----------------------------')
diffFile.close()