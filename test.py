lines = list()

import csv

with open('parsed-output.csv', 'r') as readFile:

    reader = csv.reader(readFile)

    for row in reader:
        lines.append(row)
        for field in row:
            if field == "buymybreaker" or field == "southlandelectrical" or field == "chartercontact":
                lines.remove(row)

with open('test.csv', 'w') as writeFile:

    writer = csv.writer(writeFile)

    writer.writerows(lines)