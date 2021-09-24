import csv
import json
import os
import xml.etree.ElementTree as ET
from re import match, search

files = [
    'csv_data_1.csv', 
    'csv_data_2.csv', 
    'json_data.json', 
    'xml_data.xml'
    ]
b_outp = 'basic_results.tsv'
adv_outp = 'advanced_results.tsv'
fields = []
Q_SIZE = 1000
errlog = []

def main():
    queue = list()
    row = dict()
    #объекты в виде словаря сохраняются в списке queue, пока тот не достигнет размера Q_SIZE элементов
    #при достижении этого лимита происходит вызов write_file()
    for inp in files:
        try:
            with open(inp,"r") as readfile:
                if(match(".*\.csv",inp)):
                    reader = csv.DictReader(readfile)
                    for row in reader:
                        row = to_stand(row)
                        if(row): queue.append(row)
                        if len(queue) == Q_SIZE:
                            write_file(queue)
                elif(match(".*\.json",inp)):
                    reader = json.load(readfile)
                    row = dict()
                    for row in reader["fields"]:
                        row = to_stand(row)
                        if(row): queue.append(row)
                        if len(queue) == Q_SIZE:
                            write_file(queue)
                elif(match(".*\.xml",inp)):
                    tree = ET.parse(readfile)
                    root = tree.getroot()
                    row = dict()
                    for elem in root:
                        for i in elem:
                            row.update({i.get('name'): i[0].text})
                        row = to_stand(row)
                        if(row): queue.append(row)
                        if len(queue) == Q_SIZE:
                            write_file(queue)
        except FileNotFoundError:
            errlog.append('No such file ' + inp)
    write_file(queue)
    #перенос данных из резервного файла в basic_results
    with open('inter.tsv','r') as rfile, open(b_outp, 'w') as wfile:
        inp = csv.DictReader(rfile, restval=0, delimiter='\t')
        outp = csv.DictWriter(wfile, fieldnames=fields, delimiter='\t')
        outp.writeheader()
        for row in inp:
            outp.writerow(row)
    os.remove('inter.tsv')
    #комбинирование строк и их сохранение в adv_results
    with open(b_outp,'r') as rfile, open(adv_outp,'w') as wfile:
        inp = csv.DictReader(rfile, restval=0, delimiter='\t')
        outp = csv.DictWriter(wfile, fieldnames=fields, delimiter='\t')
        outp.writeheader()
        outrow = {}
        for row in inp:
            row = to_stand(row)
            if outrow and compare(row, outrow) == 0:
                outrow = unite(row, outrow)
            else:
                if outrow: outp.writerow(outrow)
                outrow = row
        outp.writerow(outrow)
    for i in errlog:
        print(i)

#промежуточное сохранение в дополнительном файле
def write_file(queue):
    global fields
    for row in queue:
        if len(row.keys()) > len(fields):
            fields = list(row.keys())
    fields.sort(key = lambda x: ord(x[0])+int(search('\d+',x).group()))
    quick_sort(queue, 0, len(queue)-1)
    try:
        #в случае если элементов оказалось слишком много создается еще один файл, в который происходит запись слиянием
        #предыдущий файл удаляется
        with open('inter.tsv','r') as rfile, open('inter2.tsv','w') as wfile:
            inp = csv.DictReader(rfile, restval=0, delimiter='\t')
            outp = csv.DictWriter(wfile, fieldnames=fields, delimiter='\t', restval=0)
            outp.writeheader()
            res = 2
            for i in inp:
                for j in range(len(queue)):
                    res = compare(i,queue[0])
                    if res == 2:
                        outp.writerow(queue[0])
                        del queue[0]
                    else:
                        break
                outp.writerow(i)
            for i in queue:
                outp.writerow(i)
        os.remove('inter.tsv')
        os.rename('inter2.tsv', 'inter.tsv')
    except FileNotFoundError:
        with open('inter.tsv','w') as wfile:
            temp = csv.DictWriter(wfile, fieldnames=fields, delimiter='\t',restval=0)
            temp.writeheader()
            for i in range(len(queue)):
                temp.writerow(queue[0])
                del queue[0]

#функция для нахождения строк с неверными integer данными в D1...Dn
def to_stand(row):
    try:
        for i in row.keys():
            if(match("M",i)):
                row[i] = int(row[i])
        return row
    except ValueError:
        errlog.append('wrong value in row: ' + str(row))
        return {}

#Объединение элементов
def unite(a,b):
    for i in a.keys():
        if(match("M",i)):
            a[i]=a[i]+b[i]
    return a

#Сравнение элементов
def compare(a,b):
    for i in fields:
        if match('D',i):
           if(a[i]>b[i]): return 2
           elif(a[i]<b[i]): return 1
    return 0 

#Сортировка списка на основе быстрой сортировки
def quick_sort(queue, fst, lst):
    if(fst>=lst):
        return queue
    else:
        rel = queue[(fst+lst)//2]
        i, j = fst, lst
        while i<=j:
            while compare(queue[i],rel) == 1: i+=1
            while compare(queue[j],rel) == 2: j-=1
            if i<=j:
                queue[i],queue[j] = queue[j],queue[i]
                i,j=i+1,j-1
    quick_sort(queue,fst,j)
    quick_sort(queue,i,lst)
                
if __name__ == "__main__":
    main()